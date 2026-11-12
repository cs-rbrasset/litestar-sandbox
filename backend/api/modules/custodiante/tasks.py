"""Os jobs de importação e reprocessamento. Nenhum `prefect` aqui — só `core/jobs.py`.

**As etapas nunca se fundem.** Importação:

    baixar (gateway) → guardar bruto → parsear → gravar (carteira/extrato)

Reprocessamento:

    ler bruto do storage → parsear → gravar

Cada passo com efeito colateral é uma `@etapa`, com retry próprio; o job (`@job`) só orquestra
e não repete. É isso que impede uma falha tardia de refazer a coleta: se gravar o bruto falha
porque o storage piscou, repete-se **só** `guardar`, com os arquivos baixados ainda em memória
— o custodiante não é chamado de novo. O mesmo vale pro banco em `gravar_*`.

O bruto é salvo **antes** do parse — se o parse quebrar, o arquivo que quebrou ficou guardado,
e corrigir o parser não exige pedir nada de novo ao custodiante. O parse não é etapa: é função
pura, não tem o que repetir.

Erro de domínio — layout não reconhecido, carteira inválida, custodiante que não fornece aquele
documento — entra em `nao_repetir`: o arquivo é o mesmo, repetir não muda o resultado e só gasta
janela. Retry é pra falha transitória (rede, portal fora do ar, storage, banco).

O processo do job não tem app Litestar: job **não publica evento**. A passagem pra outro módulo
é chamada direta no `public.py` dele (`registrar_carteira` / `registrar_extrato`).

Parâmetros dos jobs são tipos simples de propósito: o orquestrador serializa a chamada e resolve
as anotações num processo à parte. Parâmetros das etapas podem ser objetos: vivem só em memória,
dentro da mesma execução.
"""

import datetime

from core.jobs import etapa, job, sessao_de_job
from core.storage import armazenamento_padrao
from modules.carteira.public import (
    CarteiraInvalidaError,
    CarteiraNormalizada,
    registrar_carteira,
)
from modules.custodiante.brutos import Coleta, codigo_do_prefixo, guardar_brutos, ler_brutos
from modules.custodiante.enums import CodigoCustodiante, TipoDocumento
from modules.custodiante.parsers.erros import LayoutNaoReconhecidoError
from modules.custodiante.protocols import (
    Adaptador,
    ArquivoBruto,
    DocumentoIndisponivelError,
    GatewayCustodiante,
    ParseCarteira,
    ParseExtrato,
)
from modules.custodiante.registro import CustodianteDesconhecidoError, adaptador
from modules.extrato.public import ExtratoInvalidoError, ExtratoNormalizado, registrar_extrato

#: erro de domínio: a etapa falha e fica falhada, sem repetir.
ERROS_DE_DOMINIO = (
    LayoutNaoReconhecidoError,
    CarteiraInvalidaError,
    ExtratoInvalidoError,
    DocumentoIndisponivelError,
    CustodianteDesconhecidoError,
)

#: coleta: o portal fora do ar costuma voltar em minutos, não em segundos.
TENTATIVAS_DE_COLETA = 3
INTERVALO_DE_COLETA_S = 60
#: storage: falha típica é um blip — repete rápido, porque o que está em jogo é não perder o
#: que acabou de ser baixado.
TENTATIVAS_DE_STORAGE = 5
INTERVALO_DE_STORAGE_S = 5
#: banco: conexão caída, deadlock. A gravação é upsert por chave de negócio, então repetir é
#: seguro.
TENTATIVAS_DE_GRAVACAO = 3
INTERVALO_DE_GRAVACAO_S = 10


# --- etapas -------------------------------------------------------------------------------


@etapa(
    tentativas=TENTATIVAS_DE_COLETA,
    intervalo_s=INTERVALO_DE_COLETA_S,
    nao_repetir=ERROS_DE_DOMINIO,
)
async def baixar(
    gateway: GatewayCustodiante,
    documento: TipoDocumento,
    fundo_cnpj: str,
    data: datetime.date,
) -> list[ArquivoBruto]:
    """A única etapa que fala com o custodiante."""
    if documento is TipoDocumento.CARTEIRA:
        return await gateway.baixar_carteira(fundo_cnpj, data)
    return await gateway.baixar_extrato(fundo_cnpj, data)


@etapa(tentativas=TENTATIVAS_DE_STORAGE, intervalo_s=INTERVALO_DE_STORAGE_S)
async def guardar(coleta: Coleta, arquivos: list[ArquivoBruto]) -> str:
    """Devolve o prefixo do bruto — a `referencia_origem` que a gravação carrega."""
    return await guardar_brutos(armazenamento_padrao(), coleta, arquivos)


@etapa(tentativas=TENTATIVAS_DE_STORAGE, intervalo_s=INTERVALO_DE_STORAGE_S)
async def ler(prefixo: str) -> tuple[list[ArquivoBruto], datetime.datetime]:
    return await ler_brutos(armazenamento_padrao(), prefixo)


@etapa(
    tentativas=TENTATIVAS_DE_GRAVACAO,
    intervalo_s=INTERVALO_DE_GRAVACAO_S,
    nao_repetir=ERROS_DE_DOMINIO,
)
async def gravar_carteira(
    carteira: CarteiraNormalizada,
    prefixo: str,
    coletado_em: datetime.datetime,
    *,
    forcar: bool = False,
) -> None:
    async with sessao_de_job() as sessao:
        await registrar_carteira(sessao, carteira, prefixo, coletado_em, forcar=forcar)
        await sessao.commit()


@etapa(
    tentativas=TENTATIVAS_DE_GRAVACAO,
    intervalo_s=INTERVALO_DE_GRAVACAO_S,
    nao_repetir=ERROS_DE_DOMINIO,
)
async def gravar_extrato(
    extrato: ExtratoNormalizado,
    prefixo: str,
    coletado_em: datetime.datetime,
    *,
    forcar: bool = False,
) -> None:
    async with sessao_de_job() as sessao:
        await registrar_extrato(sessao, extrato, prefixo, coletado_em, forcar=forcar)
        await sessao.commit()


# --- jobs ---------------------------------------------------------------------------------


@job("custodiante-importar-carteira")
async def importar_carteira(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    """Devolve o prefixo do bruto no storage — a `referencia_origem` gravada na carteira."""
    adaptado = adaptador(CodigoCustodiante(codigo))
    parse = _parse_carteira(adaptado)
    arquivos, prefixo, coletado_em = await _coletar(
        adaptado, TipoDocumento.CARTEIRA, fundo_cnpj, data
    )
    await gravar_carteira(parse(arquivos), prefixo, coletado_em)
    return prefixo


@job("custodiante-importar-extrato")
async def importar_extrato(codigo: str, fundo_cnpj: str, data: datetime.date) -> str:
    adaptado = adaptador(CodigoCustodiante(codigo))
    parse = _parse_extrato(adaptado)
    arquivos, prefixo, coletado_em = await _coletar(
        adaptado, TipoDocumento.EXTRATO, fundo_cnpj, data
    )
    await gravar_extrato(parse(arquivos), prefixo, coletado_em)
    return prefixo


@job("custodiante-reprocessar-carteira")
async def reprocessar_carteira(prefixo: str, forcar: bool = False) -> str:
    """Relê um bruto já guardado: corrige bug de parser ou extrai campo novo do histórico.

    Não fala com o custodiante — não existe etapa `baixar` aqui. `forcar=True` é o único jeito
    de uma releitura sobrescrever uma gravação mais recente que ela.
    """
    parse = _parse_carteira(adaptador(codigo_do_prefixo(prefixo)))
    arquivos, coletado_em = await ler(prefixo)
    await gravar_carteira(parse(arquivos), prefixo, coletado_em, forcar=forcar)
    return prefixo


@job("custodiante-reprocessar-extrato")
async def reprocessar_extrato(prefixo: str, forcar: bool = False) -> str:
    parse = _parse_extrato(adaptador(codigo_do_prefixo(prefixo)))
    arquivos, coletado_em = await ler(prefixo)
    await gravar_extrato(parse(arquivos), prefixo, coletado_em, forcar=forcar)
    return prefixo


# --- apoio --------------------------------------------------------------------------------


async def _coletar(
    adaptado: Adaptador,
    documento: TipoDocumento,
    fundo_cnpj: str,
    data: datetime.date,
) -> tuple[list[ArquivoBruto], str, datetime.datetime]:
    """Baixar → guardar. Duas etapas, não uma: cada uma repete sozinha."""
    coletado_em = datetime.datetime.now(datetime.UTC)
    arquivos = await baixar(adaptado.gateway, documento, fundo_cnpj, data)
    coleta = Coleta(
        codigo=adaptado.gateway.codigo,
        documento=documento,
        fundo_cnpj=fundo_cnpj,
        data=data,
        coletado_em=coletado_em,
    )
    prefixo = await guardar(coleta, arquivos)
    return arquivos, prefixo, coletado_em


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
