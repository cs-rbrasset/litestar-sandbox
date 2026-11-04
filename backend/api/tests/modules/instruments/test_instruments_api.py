from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar import Litestar
    from litestar.testing import TestClient


def test_list_instruments_starts_empty(app_client: TestClient[Litestar]) -> None:
    response = app_client.get("/api/v1/instruments")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_instrument_cetip_code_is_normalized(
    create_instrument: Callable[..., dict[str, Any]],
) -> None:
    instrument = create_instrument(cetip_code="  canE3 ")
    assert instrument["cetip_code"] == "CANE3"
