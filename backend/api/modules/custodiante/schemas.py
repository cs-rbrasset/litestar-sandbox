import datetime
from typing import Annotated, TypeAlias

import msgspec

from modules.custodiante.enums import CodigoCustodiante, TipoDocumento

FundoCnpj: TypeAlias = Annotated[str, msgspec.Meta(pattern=r"^\d{14}$")]  # noqa: UP040


class ImportacaoRequest(msgspec.Struct):
    codigo: CodigoCustodiante
    documento: TipoDocumento
    fundo_cnpj: FundoCnpj
    data: datetime.date


class ReprocessamentoRequest(msgspec.Struct):
    documento: TipoDocumento
    #: prefixo da coleta no object storage, devolvido pela importação
    prefixo: str
    forcar: bool = False


class ExecucaoHandle(msgspec.Struct):
    """O id vem na hora; o trabalho acontece no worker."""

    id_execucao: str


class ExecucaoStatus(msgspec.Struct):
    id_execucao: str
    estado: str
    concluido: bool
    #: prefixo do bruto quando terminou — o que foi gravado como `referencia_origem`
    referencia_origem: str | None = None
