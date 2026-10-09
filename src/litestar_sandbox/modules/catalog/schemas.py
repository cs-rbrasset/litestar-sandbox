import decimal

import msgspec


class ProductCreate(msgspec.Struct):
    name: str
    sku: str
    price: decimal.Decimal
    description: str | None = None

