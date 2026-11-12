"""Job mais longo (relatório de posições em várias datas, em PDF).

Nada de `prefect` aqui: o módulo só conhece a porta `core/jobs.py` (`@job`, `sessao_de_job`,
`id_execucao_atual`). O worker (`backend/api/worker.py`) descobre este arquivo sozinho — não
precisa registrar a task em lugar nenhum.

Roda fora do request, num processo sem app Litestar: a sessão vem de `sessao_de_job()`, que já
declara a identidade de sistema e cuida da engine (uma por execução, com dispose no fim).

O PDF vai pro object storage (`core/storage.py`); o resultado do job é só o path do objeto, e
quem pede o arquivo recebe uma signed URL curta.
"""

import dataclasses
import datetime
import io

from xhtml2pdf import pisa

from core.jobs import id_execucao_atual, job, sessao_de_job
from core.storage import armazenamento_padrao
from modules.posicoes.domain import Position  # noqa: TC001
from modules.posicoes.services import PositionService

# o orquestrador serializa o job pra rodar num worker à parte e resolve __annotate__ do
# dataclass fora do módulo original: em TYPE_CHECKING, "Position" não existe nesse momento.


@dataclasses.dataclass(frozen=True)
class DatedPositions:
    reference_date: datetime.date
    positions: list[Position]


async def _positions_at(fund_cnpj: str, reference_date: datetime.date) -> DatedPositions:
    async with sessao_de_job() as session:
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


@job("recompute-positions-report")
async def recompute_positions_report(fund_cnpj: str, reference_dates: list[datetime.date]) -> str:
    """Devolve o path do PDF no bucket (não o PDF em si): o front pede a signed URL à parte."""
    dated = [await _positions_at(fund_cnpj, d) for d in reference_dates]
    pdf_bytes = _html_to_pdf(_render_html(fund_cnpj, dated))
    path = f"reports/{id_execucao_atual()}.pdf"
    await armazenamento_padrao().put(path, pdf_bytes, "application/pdf")
    return path
