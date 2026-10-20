from typing import Annotated, TypeAlias

import msgspec

from litestar_sandbox.modules.instruments.enums import InstrumentType

InstrumentName: TypeAlias = Annotated[str, msgspec.Meta(min_length=1, max_length=200)]  # noqa: UP040
InstrumentCETIPCode: TypeAlias = Annotated[  # noqa: UP040
    str, msgspec.Meta(pattern=r"(?i)^\s*[A-Z0-9]{4,20}\s*$")
]


class InstrumentCreate(msgspec.Struct):
    name: InstrumentName
    cetip_code: InstrumentCETIPCode
    instrument_type: InstrumentType


class InstrumentUpdate(msgspec.Struct):
    name: InstrumentName | msgspec.UnsetType = msgspec.UNSET
