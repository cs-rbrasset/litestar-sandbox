from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient


def test_list_products_starts_empty(app_client: TestClient[Litestar]) -> None:
    response = app_client.get("/catalog/products")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def create_product(app_client: TestClient[Litestar], **overrides: str) -> dict:
    payload = {"name": "caneta azul", "sku": "CA-N3-74", "price": "10.00", "description": "AZUL CANETA"} | overrides
    return app_client.post("/catalog/products", data=payload).json()


def test_product_sku_is_normalized(app_client: TestClient[Litestar]) -> None:
    product = create_product(app_client, sku="  AA-B1-00  ")
    assert product["sku"] == "AA-B1-00"

