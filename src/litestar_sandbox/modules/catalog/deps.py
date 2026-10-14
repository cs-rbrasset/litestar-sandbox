from typing import TYPE_CHECKING, TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from litestar_sandbox.modules.catalog.protocols import ProductServiceProtocol

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.providers import FilterConfig

ProductServiceDep: TypeAlias = NamedDependency[SkipValidation[ProductServiceProtocol]]

product_filter_config: FilterConfig = {
    "pagination_type": "limit_offset",
    "search": "name",
    "sort_field": "created_at",
    "sort_order": "desc",
}
