"""Job mais longo (relatório de posições em várias datas, em PDF) via Prefect background tasks.

Sem flow nem deployment: `.delay()` cria o task run direto a partir da task; o worker
(`prefect.task_worker.serve`, chamado aqui por `.serve()`) executa. Mais simples que o
flow+deployment que usávamos antes, e é exatamente pra isso que o recurso existe.

Roda fora do request, num worker à parte (sem app do Litestar no processo): abre a própria
sessão com create_sqlalchemy_config(DatabaseSettings.from_env()), como os listeners, faz
commit à mão (aqui só leitura, mas a sessão segue o mesmo padrão) e é idempotente.

O Prefect guarda o estado da execução (histórico, retry) sozinho: não existe tabela própria
de "jobs" nem um dispatcher — o controller só chama .delay() e consulta pelo client. O PDF em
si vai pro Supabase Storage (core/storage.py); o resultado da task é só o path do objeto.

Pré-requisitos (fora deste processo):
  - server: prefect server start   (ou PREFECT_API_URL apontando para um já no ar)
  - worker: uv run --env-file .env python -m modules.positions.tasks
            (--env-file é obrigatório: ao contrário de "litestar run", um "python -m" solto
            não carrega o .env sozinho)
"""

import dataclasses
import datetime
import io

from prefect import task
from prefect.runtime import task_run
from xhtml2pdf import pisa

from core.database import create_sqlalchemy_config
from core.identity import SYSTEM, use_identity
from core.settings import DatabaseSettings, SupabaseSettings
from core.storage import upload_object
from modules.positions.domain import Position  # noqa: TC001
from modules.positions.services import PositionService

# o Prefect serializa a task pra rodar num worker à parte e resolve __annotate__ do dataclass
# fora do módulo original: em TYPE_CHECKING, "Position" não existe nesse momento e quebra.


@dataclasses.dataclass(frozen=True)
class DatedPositions:
    reference_date: datetime.date
    positions: list[Position]


async def _positions_at(fund_cnpj: str, reference_date: datetime.date) -> DatedPositions:
    settings = DatabaseSettings.from_env()
    config = create_sqlalchemy_config(settings)
    with use_identity(SYSTEM):
        async with config.get_session() as session:
            service = PositionService(session=session)
            positions = await service.positions_at(fund_cnpj, reference_date)
    return DatedPositions(reference_date=reference_date, positions=positions)


def _render_html(fund_cnpj: str, dated: list[DatedPositions]) -> str:
    sections = "".join(
        f"<h2>{d.reference_date.isoformat()}</h2>"
        + (
            "<p>Sem posição nessa data.</p>"
            if not d.positions
            else "<table><thead><tr><th>Ativo</th><th>Quantidade</th></tr></thead><tbody>"
            + "".join(
                f"<tr><td>{p.cetip_code}</td><td class='num'>{p.quantity}</td></tr>"
                for p in d.positions
            )
            + "</tbody></table>"
        )
        for d in dated
    )
    return f"""<html>
<head><style>
  body {{ font-family: Helvetica, sans-serif; font-size: 11pt; }}
  table {{ width: 100%; margin-bottom: 16pt; }}
  th, td {{ border: 1px solid #ccc; padding: 4pt 8pt; }}
  th {{ background: #f0f0f0; text-align: left; }}
  td.num {{ text-align: right; }}
</style></head>
<body>
  <h1>Relatório de posições &mdash; fundo {fund_cnpj}</h1>
  {sections}
</body>
</html>"""


def _html_to_pdf(html: str) -> bytes:
    buffer = io.BytesIO()
    result = pisa.CreatePDF(html, dest=buffer)
    if result.err:
        msg = "falha ao gerar PDF do relatório de posições"
        raise RuntimeError(msg)
    return buffer.getvalue()


@task(name="recompute-positions-report", persist_result=True)
async def recompute_positions_report(fund_cnpj: str, reference_dates: list[datetime.date]) -> str:
    """Devolve o path do PDF no bucket (não o PDF em si): o front pede a signed URL à parte."""
    dated = [await _positions_at(fund_cnpj, reference_date) for reference_date in reference_dates]
    pdf_bytes = _html_to_pdf(_render_html(fund_cnpj, dated))
    path = f"reports/{task_run.id}.pdf"
    await upload_object(SupabaseSettings.from_env(), path, pdf_bytes, content_type="application/pdf")
    return path


if __name__ == "__main__":
    recompute_positions_report.serve()
