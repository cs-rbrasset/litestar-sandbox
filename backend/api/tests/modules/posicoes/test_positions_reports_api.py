"""Relatório de posições pela porta `core/jobs.py` — sem server nem worker no ar no teste.

Os dublês trocam exatamente a fronteira que o módulo conhece (`enfileirar`, `status`,
armazenamento), nunca o client do orquestrador: se alguém reintroduzir `prefect` dentro do
módulo, estes testes continuam passando e o `lint-imports` é que acusa.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any

import pytest

from core.jobs import EstadoJob, ExecucaoNaoEncontradaError, OrquestradorIndisponivelError
from core.storage import ArmazenamentoEmMemoria
from modules.posicoes import controllers as positions_controllers
from modules.posicoes import services as positions_services

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

FUND_CNPJ = "12345678000190"


@pytest.fixture
def fake_enfileirar(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    chamadas: dict[str, Any] = {"task_run_id": str(uuid.uuid4())}

    async def _enfileirar(_job: Any, **parametros: Any) -> str:
        chamadas["parametros"] = parametros
        return chamadas["task_run_id"]

    monkeypatch.setattr(positions_services, "enfileirar", _enfileirar)
    return chamadas


def _com_status(monkeypatch: pytest.MonkeyPatch, estado: EstadoJob) -> None:
    async def _status(task_run_id: str) -> EstadoJob:
        return estado

    monkeypatch.setattr(positions_controllers, "status", _status)


def test_trigger_report_schedules_background_job(
    app_client: TestClient[Litestar], fake_enfileirar: dict[str, Any]
) -> None:
    response = app_client.post(
        "/api/v1/posicoes/reports",
        json={"fund_cnpj": FUND_CNPJ, "reference_dates": ["2026-10-01", "2026-10-02"]},
    )

    assert response.status_code == 202, response.text
    assert response.json() == {"task_run_id": fake_enfileirar["task_run_id"]}
    assert fake_enfileirar["parametros"] == {
        "fund_cnpj": FUND_CNPJ,
        "reference_dates": [datetime.date(2026, 10, 1), datetime.date(2026, 10, 2)],
    }


def test_trigger_report_503_when_orchestrator_unreachable(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _indisponivel(_job: Any, **parametros: Any) -> str:
        raise OrquestradorIndisponivelError("connection refused")

    monkeypatch.setattr(positions_services, "enfileirar", _indisponivel)

    response = app_client.post(
        "/api/v1/posicoes/reports",
        json={"fund_cnpj": FUND_CNPJ, "reference_dates": ["2026-10-01"]},
    )

    assert response.status_code == 503, response.text
    assert "orquestrador" in response.json()["detail"]


def test_get_report_returns_completed_state(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    _com_status(
        monkeypatch,
        EstadoJob(
            id="some-task-run-id",
            estado="COMPLETED",
            concluido=True,
            resultado="reports/some-task-run-id.pdf",
        ),
    )

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id")

    assert response.status_code == 200, response.text
    assert response.json() == {"task_run_id": "some-task-run-id", "state": "COMPLETED"}


def test_get_report_404_when_execution_unknown(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _nao_encontrada(task_run_id: str) -> EstadoJob:
        raise ExecucaoNaoEncontradaError(task_run_id)

    monkeypatch.setattr(positions_controllers, "status", _nao_encontrada)

    response = app_client.get("/api/v1/posicoes/reports/does-not-exist")

    assert response.status_code == 404, response.text


def test_get_report_returns_running_state(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    _com_status(
        monkeypatch, EstadoJob(id="some-task-run-id", estado="RUNNING", concluido=False)
    )

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id")

    assert response.status_code == 200, response.text
    assert response.json() == {"task_run_id": "some-task-run-id", "state": "RUNNING"}


def test_get_report_pdf_returns_signed_url_when_completed(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    caminho = "reports/some-task-run-id.pdf"
    _com_status(
        monkeypatch,
        EstadoJob(id="some-task-run-id", estado="COMPLETED", concluido=True, resultado=caminho),
    )
    armazenamento = ArmazenamentoEmMemoria()
    armazenamento.objetos[caminho] = b"%PDF-fake"
    monkeypatch.setattr(positions_controllers, "armazenamento_padrao", lambda: armazenamento)

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id/pdf")

    assert response.status_code == 200, response.text
    assert response.json() == {"url": f"memoria://{caminho}?expira_em=3600"}


def test_get_report_pdf_conflicts_while_not_completed(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    _com_status(
        monkeypatch, EstadoJob(id="some-task-run-id", estado="RUNNING", concluido=False)
    )

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id/pdf")

    assert response.status_code == 409, response.text
