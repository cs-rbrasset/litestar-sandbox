from typing import TYPE_CHECKING, TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from litestar_sandbox.modules.instruments.protocols import InstrumentServiceProtocol

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.providers import FilterConfig

InstrumentServiceDep: TypeAlias = NamedDependency[SkipValidation[InstrumentServiceProtocol]]

instrument_filter_config: FilterConfig = {
    "pagination_type": "limit_offset",
    "search": "name",
    "sort_field": "created_at",
    "sort_order": "desc",
}
