import datetime
from typing import Annotated, TypeAlias

import msgspec

FundCnpj: TypeAlias = Annotated[str, msgspec.Meta(pattern=r"^\d{14}$")]  # noqa: UP040


class PositionsReportRequest(msgspec.Struct):
    fund_cnpj: FundCnpj
    reference_dates: list[datetime.date]


class PositionsReportHandle(msgspec.Struct):
    """Devolvida ao agendar: o estado de verdade mora no orquestrador, não aqui."""

    task_run_id: str


class PositionsReportStatus(msgspec.Struct):
    """O PDF não vai aqui: pronto, busca a signed URL em /reports/{task_run_id}/pdf."""

    task_run_id: str
    state: str


class PositionsReportPdfUrl(msgspec.Struct):
    """Signed URL do object storage, curta (1h): o front baixa direto de lá, sem passar por aqui."""

    url: str
