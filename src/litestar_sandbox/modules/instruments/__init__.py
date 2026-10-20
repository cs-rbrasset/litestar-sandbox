from litestar import Router

from litestar_sandbox.modules.instruments.controllers import InstrumentController

instruments_router = Router(path="/instruments", route_handlers=[InstrumentController])
