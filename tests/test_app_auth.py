from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

if TYPE_CHECKING:
    from collections.abc import Iterator

    from litestar import Litestar


@pytest.fixture
def anonymous_client(app: Litestar) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app) as client:
        yield client


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/instruments"),
        ("POST", "/api/v1/instruments"),
        ("GET", "/api/v1/trades"),
        ("POST", "/api/v1/trades/1/settle"),
        ("GET", "/api/v1/positions?fund_cnpj=12345678000190&reference_date=2026-10-20"),
    ],
)
def test_api_requires_token(anonymous_client: TestClient[Litestar], method: str, path: str) -> None:
    assert anonymous_client.request(method, path).status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/ping", "/api/v1/schema/openapi.json"])
def test_ping_and_openapi_are_public(anonymous_client: TestClient[Litestar], path: str) -> None:
    assert anonymous_client.get(path).status_code == 200
