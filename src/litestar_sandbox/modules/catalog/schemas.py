import decimal

import msgspec


class ProductCreate(msgspec.Struct):
    name: str
    sku: str
    price: decimal.Decimal  # no swagger será identificado como string
    description: str | None = None
