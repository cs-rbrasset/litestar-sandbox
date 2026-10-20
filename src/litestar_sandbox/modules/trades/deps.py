from typing import TYPE_CHECKING, TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from litestar_sandbox.modules.instruments.public import InstrumentPublicAPI
from litestar_sandbox.modules.trades.protocols import TradeServiceProtocol

if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.providers import FilterConfig

TradeServiceDep: TypeAlias = NamedDependency[SkipValidation[TradeServiceProtocol]]
InstrumentPublicAPIDep: TypeAlias = NamedDependency[SkipValidation[InstrumentPublicAPI]]

trade_filter_config: FilterConfig = {
    "pagination_type": "limit_offset",
    "search": {"fund_cnpj", "cetip_code"},
    "sort_field": "trade_date",
    "sort_order": "desc",
}
