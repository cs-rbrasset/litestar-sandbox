import decimal
from typing import Annotated, TypeAlias

import msgspec

InstrumentName: TypeAlias = Annotated[str, msgspec.Meta(min_length=1, max_length=200)]  # noqa: UP040
InstrumentSku: TypeAlias = Annotated[  # noqa: UP040
    str, msgspec.Meta(pattern=r"(?i)^\s*[A-Z]{2,3}-[A-Z0-9]{2,4}-[0-9]{2}\s*$")
]
InstrumentDescription: TypeAlias = Annotated[str, msgspec.Meta(min_length=1)]  # noqa: UP040


class InstrumentCreate(msgspec.Struct):
    name: InstrumentName
    sku: InstrumentSku
    price: decimal.Decimal  # no swagger será identificado como string
    description: InstrumentDescription | None = None

    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("Preço igual ou menor que zero")


class InstrumentUpdate(msgspec.Struct):
    name: InstrumentName | msgspec.UnsetType = msgspec.UNSET
    price: decimal.Decimal | msgspec.UnsetType = msgspec.UNSET
    description: InstrumentDescription | msgspec.UnsetType | None = msgspec.UNSET

    def __post_init__(self):
        if self.price is not msgspec.UNSET and self.price <= 0:
            raise ValueError("Preço igual ou menor que zero")
