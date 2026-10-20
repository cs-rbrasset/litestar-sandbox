from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient


def test_list_instruments_starts_empty(app_client: TestClient[Litestar]) -> None:
    response = app_client.get("/api/v1/instruments")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def create_instrument(app_client: TestClient[Litestar], **overrides: str) -> dict:
    payload = {
        "name": "caneta azul",
        "cetip_code": "CANE4",
        "instrument_type": "CRI",
    } | overrides
    return app_client.post("/api/v1/instruments", data=payload).json()


def test_instrument_cetip_code_is_normalized(app_client: TestClient[Litestar]) -> None:
    instrument = create_instrument(app_client, cetip_code="  canE3 ")
    assert instrument["cetip_code"] == "CANE3"
