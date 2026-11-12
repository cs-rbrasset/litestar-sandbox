"""Os jobs de importação e reprocessamento. Nenhum `prefect` aqui — só `core/jobs.py`.

**As etapas nunca se fundem.** Importação:

    baixar (gateway) → guardar bruto → parsear → registrar (carteira/extrato)

Reprocessamento:

    ler bruto do storage → parsear → registrar

Baixar e parsear são sempre duas chamadas separadas, orquestradas aqui. O bruto é salvo
**antes** do parse — se o parse quebrar, o arquivo que quebrou ficou guardado, e corrigir o
parser não exige pedir nada de novo ao custodiante.

Retry é só pra **falha de coleta** (rede, portal fora do ar). Erro de domínio — layout não
reconhecido, carteira inválida, custodiante que não fornece aquele documento — entra em
`nao_repetir`: o arquivo é o mesmo, repetir não muda o resultado e só gasta janela.

O worker não tem app Litestar: job **não publica evento**. A passagem pra outro módulo é
chamada direta no `public.py` dele (`registrar_carteira` / `registrar_extrato`).

Parâmetros são tipos simples de propósito: o orquestrador serializa a chamada e resolve as
anotações num processo à parte.
"""

import datetime

from core.jobs import job, sessao_de_job
from core.storage import armazenamento_padrao
from modules.carteira.public import CarteiraInvalidaError, registrar_carteira
from modules.custodiante.brutos import Coleta, codigo_do_prefixo, guardar_brutos, ler_brutos
from modules.custodiante.enums import CodigoCustodiante, TipoDocumento
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError
from modules.custodiante.protocols import (
    Adaptador,
    DocumentoIndisponivelError,
    ParseCarteira,
    ParseExtrato,
)
from modules.custodiante.registro import CustodianteDesconhecidoError, adaptador
from modules.extrato.public import ExtratoInvalidoError, registrar_extrato

#: erro de domínio: o job falha e fica falhado, sem repetir.
ERROS_DE_DOMINIO = (
    LayoutNaoReconhecidoError,
    CarteiraInvalidaError,
    ExtratoInvalidoError,
    DocumentoIndisponivelError,
    CustodianteDesconhecidoError,
)

TENTATIVAS_DE_COLETA = 3
INTERVALO_ENTRE_TENTATIVAS_S = 60


@job(
    "custodiante-importar-carteira",
    tentativas=TENTATIVAS_DE_COLETA,
    intervalo_s=INTERVALO_ENTRE_TENTATIVAS_S,
    nao_repetir=ERROS_DE_DOMINIO,
)
async def importar_carteira(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    """Devolve o prefixo do bruto no storage — a `referencia_origem` gravada na carteira."""
    adaptado = adaptador(CodigoCustodiante(codigo))
    parse = _parse_carteira(adaptado)
    coletado_em = datetime.datetime.now(datetime.UTC)

    arquivos = await adaptado.gateway.baixar_carteira(fundo_cnpj, data)
    coleta = Coleta(
        codigo=adaptado.gateway.codigo,
        documento=TipoDocumento.CARTEIRA,
        fundo_cnpj=fundo_cnpj,
        data=data,
        coletado_em=coletado_em,
    )
    prefixo = await guardar_brutos(armazenamento_padrao(), coleta, arquivos)
    canonica = parse(arquivos)
    async with sessao_de_job() as sessao:
        await registrar_carteira(sessao, canonica, prefixo, coletado_em)
        await sessao.commit()
    return prefixo


@job(
    "custodiante-importar-extrato",
    tentativas=TENTATIVAS_DE_COLETA,
    intervalo_s=INTERVALO_ENTRE_TENTATIVAS_S,
    nao_repetir=ERROS_DE_DOMINIO,
)
async def importar_extrato(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    adaptado = adaptador(CodigoCustodiante(codigo))
    parse = _parse_extrato(adaptado)
    coletado_em = datetime.datetime.now(datetime.UTC)

    arquivos = await adaptado.gateway.baixar_extrato(fundo_cnpj, data)
    coleta = Coleta(
        codigo=adaptado.gateway.codigo,
        documento=TipoDocumento.EXTRATO,
        fundo_cnpj=fundo_cnpj,
        data=data,
        coletado_em=coletado_em,
    )
    prefixo = await guardar_brutos(armazenamento_padrao(), coleta, arquivos)
    canonico = parse(arquivos)
    async with sessao_de_job() as sessao:
        await registrar_extrato(sessao, canonico, prefixo, coletado_em)
        await sessao.commit()
    return prefixo


@job("custodiante-reprocessar-carteira", nao_repetir=ERROS_DE_DOMINIO)
async def reprocessar_carteira(prefixo: str, forcar: bool = False) -> str:
    """Relê um bruto já guardado: corrige bug de parser ou extrai campo novo do histórico.

    Não fala com o custodiante — por isso não tem retry de coleta. `forcar=True` é o único jeito
    de uma releitura sobrescrever uma gravação mais recente que ela.
    """
    adaptado = adaptador(codigo_do_prefixo(prefixo))
    parse = _parse_carteira(adaptado)
    arquivos, coletado_em = await ler_brutos(armazenamento_padrao(), prefixo)
    canonica = parse(arquivos)
    async with sessao_de_job() as sessao:
        await registrar_carteira(sessao, canonica, prefixo, coletado_em, forcar=forcar)
        await sessao.commit()
    return prefixo


@job("custodiante-reprocessar-extrato", nao_repetir=ERROS_DE_DOMINIO)
async def reprocessar_extrato(prefixo: str, forcar: bool = False) -> str:
    adaptado = adaptador(codigo_do_prefixo(prefixo))
    parse = _parse_extrato(adaptado)
    arquivos, coletado_em = await ler_brutos(armazenamento_padrao(), prefixo)
    canonico = parse(arquivos)
    async with sessao_de_job() as sessao:
        await registrar_extrato(sessao, canonico, prefixo, coletado_em, forcar=forcar)
        await sessao.commit()
    return prefixo


def _parse_carteira(adaptado: Adaptador) -> ParseCarteira:
    if adaptado.parse_carteira is None:
        msg = f"{adaptado.gateway.codigo} não fornece carteira"
        raise DocumentoIndisponivelError(msg)
    return adaptado.parse_carteira


def _parse_extrato(adaptado: Adaptador) -> ParseExtrato:
    if adaptado.parse_extrato is None:
        msg = f"{adaptado.gateway.codigo} não fornece extrato"
        raise DocumentoIndisponivelError(msg)
    return adaptado.parse_extrato
