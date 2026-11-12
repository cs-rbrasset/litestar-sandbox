"""O arquivo bruto pertence ao `custodiante` — é o registro do que o custodiante mandou.

Não é uma carteira: é prova. Guardado **antes** do parse, nunca sobrescrito, e com um
`manifesto.json` ao lado dizendo o que veio, com que hash e quando. É isso que torna o
reprocessamento possível (corrigir um parser e reler o histórico sem chamar o custodiante).

Layout no object storage:

    custodiante/{codigo}/{documento}/{cnpj}/{data}/{coletado_em}_{hash}/
        manifesto.json
        <arquivos como vieram>
        falhas/           # HTML e screenshot quando a coleta quebra (scraping)

Cada coleta tem prefixo próprio (`coletado_em` + hash do conteúdo): duas coletas do mesmo dia
coexistem, e uma coleta repetida com conteúdo idêntico cai no mesmo prefixo.

[AJUSTAR: prazo de retenção] — definir com compliance e aplicar como regra de ciclo de vida do
bucket, não como código de limpeza aqui.
"""

import dataclasses
import datetime
import hashlib
import json
from typing import TYPE_CHECKING

from core.storage import juntar
from modules.custodiante.enums import CodigoCustodiante
from modules.custodiante.protocols import ArquivoBruto

if TYPE_CHECKING:
    from collections.abc import Sequence

    from core.storage import Armazenamento
    from modules.custodiante.enums import TipoDocumento

MANIFESTO = "manifesto.json"


@dataclasses.dataclass(frozen=True, slots=True)
class Coleta:
    """Identidade de uma coleta: o que foi buscado, de quem, de quando, e quando foi buscado."""

    codigo: CodigoCustodiante
    documento: TipoDocumento
    fundo_cnpj: str
    data: datetime.date
    coletado_em: datetime.datetime


def prefixo_da_coleta(coleta: Coleta, arquivos: Sequence[ArquivoBruto]) -> str:
    marca = coleta.coletado_em.strftime("%Y%m%dT%H%M%SZ")
    return juntar(
        "custodiante",
        coleta.codigo.value,
        coleta.documento.value,
        coleta.fundo_cnpj,
        coleta.data.isoformat(),
        f"{marca}_{_hash_do_conjunto(arquivos)}",
    )


async def guardar_brutos(
    armazenamento: Armazenamento, coleta: Coleta, arquivos: Sequence[ArquivoBruto]
) -> str:
    """Grava os arquivos e o manifesto; devolve o prefixo (a `referencia_origem` da gravação)."""
    prefixo = prefixo_da_coleta(coleta, arquivos)
    for arquivo in arquivos:
        await armazenamento.put(
            juntar(prefixo, arquivo.nome), arquivo.conteudo, _tipo_mime(arquivo.formato)
        )
    manifesto = {
        "codigo": coleta.codigo.value,
        "documento": coleta.documento.value,
        "fundo_cnpj": coleta.fundo_cnpj,
        "data": coleta.data.isoformat(),
        "coletado_em": coleta.coletado_em.isoformat(),
        "arquivos": [
            {
                "nome": arquivo.nome,
                "formato": arquivo.formato,
                "sha256": hashlib.sha256(arquivo.conteudo).hexdigest(),
                "bytes": len(arquivo.conteudo),
            }
            for arquivo in arquivos
        ],
    }
    await armazenamento.put(
        juntar(prefixo, MANIFESTO),
        json.dumps(manifesto, ensure_ascii=False, indent=2).encode(),
        "application/json",
    )
    return prefixo


async def ler_brutos(
    armazenamento: Armazenamento, prefixo: str
) -> tuple[list[ArquivoBruto], datetime.datetime]:
    """Devolve os arquivos daquela coleta e **a hora original dela** (vinda do manifesto).

    Reprocessar não é coletar de novo: a hora original é o que mantém a precedência correta na
    hora de gravar — um reprocessamento não pode fingir ser mais recente que uma coleta nova.
    """
    manifesto = json.loads(await armazenamento.get(juntar(prefixo, MANIFESTO)))
    arquivos = [
        ArquivoBruto(
            nome=item["nome"],
            conteudo=await armazenamento.get(juntar(prefixo, item["nome"])),
            formato=item["formato"],
        )
        for item in manifesto["arquivos"]
    ]
    return arquivos, datetime.datetime.fromisoformat(manifesto["coletado_em"])


def codigo_do_prefixo(prefixo: str) -> CodigoCustodiante:
    """Lê o custodiante de volta do caminho — por isso o código vem antes de tudo no layout.

    Reprocessar recebe só o prefixo; sem isso, precisaria de um parâmetro redundante que
    poderia divergir do bruto que está sendo relido.
    """
    partes = prefixo.strip("/").split("/")
    minimo_de_partes = 2
    if len(partes) < minimo_de_partes or partes[0] != "custodiante":
        msg = f"prefixo fora do layout esperado: {prefixo!r}"
        raise ValueError(msg)
    return CodigoCustodiante(partes[1])


async def guardar_falha(
    armazenamento: Armazenamento, prefixo: str, nome: str, conteudo: bytes, formato: str
) -> str:
    """HTML/screenshot do momento do erro — sem isso não dá pra saber depois o que o portal fez."""
    caminho = juntar(prefixo, "falhas", nome)
    await armazenamento.put(caminho, conteudo, _tipo_mime(formato))
    return caminho


def _hash_do_conjunto(arquivos: Sequence[ArquivoBruto]) -> str:
    digestor = hashlib.sha256()
    for arquivo in sorted(arquivos, key=lambda a: a.nome):
        digestor.update(arquivo.nome.encode())
        digestor.update(hashlib.sha256(arquivo.conteudo).digest())
    return digestor.hexdigest()[:12]


def _tipo_mime(formato: str) -> str:
    return {
        "xml": "application/xml",
        "html": "text/html",
        "csv": "text/csv",
        "json": "application/json",
        "pdf": "application/pdf",
        "png": "image/png",
    }.get(formato, "application/octet-stream")
