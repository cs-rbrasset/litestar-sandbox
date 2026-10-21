import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litestar import Litestar

logger = logging.getLogger(__name__)


def publish(app: Litestar, event_id: str, event: object) -> None:
    """Emite o evento passando o app, para o listener achar a config do banco."""
    if app.event_emitter.listeners.get(event_id):
        app.emit(event_id, event, app=app)
    else:
        logger.warning("no event listener for event %s, discarded", event_id)
