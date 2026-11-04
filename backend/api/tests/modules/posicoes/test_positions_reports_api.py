import datetime
import uuid
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from prefect.client.schemas.objects import StateType
from prefect.exceptions import ObjectNotFound

from modules.posicoes import controllers as positions_controllers
from modules.posicoes import listeners as positions_listeners

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

FUND_CNPJ = "12345678000190"


class _FakeFuture:
    def __init__(self, task_run_id: uuid.UUID) -> None:
        self.task_run_id = task_run_id


@pytest.fixture
def fake_delay(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Troca a chamada ao Prefect por um dublê: sem server/worker no ar no teste."""
    calls: dict[str, Any] = {"task_run_id": uuid.uuid4()}

    def _fake_delay(**kwargs: Any) -> _FakeFuture:
        calls["kwargs"] = kwargs
        return _FakeFuture(calls["task_run_id"])

    monkeypatch.setattr(
        positions_listeners.recompute_positions_report, "delay", _fake_delay
    )
    return calls


def test_trigger_report_schedules_background_task(
    app_client: TestClient[Litestar], fake_delay: dict[str, Any]
) -> None:
    response = app_client.post(
        "/api/v1/posicoes/reports",
        json={"fund_cnpj": FUND_CNPJ, "reference_dates": ["2026-10-01", "2026-10-02"]},
    )

    assert response.status_code == 202, response.text
    assert response.json() == {"task_run_id": str(fake_delay["task_run_id"])}
    assert fake_delay["kwargs"] == {
        "fund_cnpj": FUND_CNPJ,
        "reference_dates": [datetime.date(2026, 10, 1), datetime.date(2026, 10, 2)],
    }


def test_trigger_report_503_when_prefect_unreachable(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    def _unreachable(**kwargs: Any) -> Any:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(positions_listeners.recompute_positions_report, "delay", _unreachable)

    response = app_client.post(
        "/api/v1/posicoes/reports",
        json={"fund_cnpj": FUND_CNPJ, "reference_dates": ["2026-10-01"]},
    )

    assert response.status_code == 503, response.text
    assert "Prefect" in response.json()["detail"]


class _FakeState:
    def __init__(self, *, completed: bool, result_value: Any) -> None:
        self._completed = completed
        self._result_value = result_value

    def is_completed(self) -> bool:
        return self._completed

    async def aresult(self, raise_on_failure: bool = True) -> Any:
        return self._result_value


class _FakeTaskRunDetail:
    def __init__(self, *, state_type: Any, state: Any) -> None:
        self.state_type = state_type
        self.state = state


class _FakeClient:
    def __init__(self, task_run: _FakeTaskRunDetail) -> None:
        self._task_run = task_run

    async def __aenter__(self) -> _FakeClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def read_task_run(self, task_run_id: str) -> _FakeTaskRunDetail:
        return self._task_run


def test_get_report_returns_completed_state(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    task_run = _FakeTaskRunDetail(
        state_type=StateType.COMPLETED,
        state=_FakeState(completed=True, result_value="reports/some-task-run-id.pdf"),
    )
    monkeypatch.setattr(positions_controllers, "get_client", lambda: _FakeClient(task_run))

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id")

    assert response.status_code == 200, response.text
    assert response.json() == {"task_run_id": "some-task-run-id", "state": "COMPLETED"}


def test_get_report_404_when_task_run_unknown(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    class _NotFoundClient:
        async def __aenter__(self) -> _NotFoundClient:
            return self

        async def __aexit__(self, *exc: Any) -> None:
            return None

        async def read_task_run(self, task_run_id: str) -> Any:
            raise ObjectNotFound(http_exc=Exception("404"))

    monkeypatch.setattr(positions_controllers, "get_client", _NotFoundClient)

    response = app_client.get("/api/v1/posicoes/reports/does-not-exist")

    assert response.status_code == 404, response.text


def test_get_report_returns_running_state(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    task_run = _FakeTaskRunDetail(
        state_type=StateType.RUNNING,
        state=_FakeState(completed=False, result_value=None),
    )
    monkeypatch.setattr(positions_controllers, "get_client", lambda: _FakeClient(task_run))

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id")

    assert response.status_code == 200, response.text
    assert response.json() == {"task_run_id": "some-task-run-id", "state": "RUNNING"}


def test_get_report_pdf_returns_signed_url_when_completed(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    task_run = _FakeTaskRunDetail(
        state_type=StateType.COMPLETED,
        state=_FakeState(completed=True, result_value="reports/some-task-run-id.pdf"),
    )
    monkeypatch.setattr(positions_controllers, "get_client", lambda: _FakeClient(task_run))

    async def _fake_create_signed_url(settings: Any, path: str, expires_in: int = 3600) -> str:
        return f"https://storage.example/{path}?token=fake"

    monkeypatch.setattr(positions_controllers, "create_signed_url", _fake_create_signed_url)
    monkeypatch.setenv("SUPABASE_URL", "https://storage.example")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
    monkeypatch.setenv("SUPABASE_STORAGE_BUCKET", "PDF")

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id/pdf")

    assert response.status_code == 200, response.text
    assert response.json() == {"url": "https://storage.example/reports/some-task-run-id.pdf?token=fake"}


def test_get_report_pdf_conflicts_while_not_completed(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    task_run = _FakeTaskRunDetail(
        state_type=StateType.RUNNING,
        state=_FakeState(completed=False, result_value=None),
    )
    monkeypatch.setattr(positions_controllers, "get_client", lambda: _FakeClient(task_run))

    response = app_client.get("/api/v1/posicoes/reports/some-task-run-id/pdf")

    assert response.status_code == 409, response.text
