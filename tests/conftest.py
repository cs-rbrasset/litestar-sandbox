from typing import TYPE_CHECKING

import pytest
from litestar.testing import TestClient

from litestar_sandbox.app import create_app
from litestar_sandbox.core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from litestar import Litestar


@pytest.fixture
def database_settings(tmp_path: Path) -> DatabaseSettings:
    return DatabaseSettings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def app(database_settings: DatabaseSettings) -> Litestar:
    return create_app(database_settings)


@pytest.fixture
def app_client(app: Litestar) -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app) as client:
        yield client
