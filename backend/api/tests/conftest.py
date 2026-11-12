import asyncio
from typing import TYPE_CHECKING, Any

import pytest
from advanced_alchemy.base import orm_registry
from litestar.testing import TestClient
from prefect.settings import PREFECT_LOCAL_STORAGE_PATH, temporary_settings
from prefect.testing.utilities import prefect_test_harness

from app import create_app
from core.auth import DevTokenVerifier
from core.database import create_sqlalchemy_config
from core.identity import SYSTEM, Identity, use_identity
from core.settings import DatabaseSettings

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator
    from pathlib import Path

    import httpx
    from litestar import Litestar
    from sqlalchemy.ext.asyncio import AsyncSession

FUND_CNPJ = "12345678000190"


@pytest.fixture(scope="session")
def orquestrador(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Server do orquestrador temporário, pra teste que **executa** um job de verdade.

    Caro (~15s pra subir), por isso uma vez por sessão e só pra quem pede: é o único jeito de
    provar o retry por etapa, que é do orquestrador, não do nosso código. Os resultados
    persistidos vão pro `tmp`, não pro `~/.prefect` de quem roda.
    """
    resultados = tmp_path_factory.mktemp("resultados-de-jobs")
    with temporary_settings({PREFECT_LOCAL_STORAGE_PATH: resultados}), prefect_test_harness():
        yield


@pytest.fixture
def database_settings(tmp_path: Path) -> DatabaseSettings:
    return DatabaseSettings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")


TEST_TOKEN = "token-de-teste"
TEST_IDENTITY = Identity(subject="u_teste", db_role="u_teste", name="Pessoa de Teste")


@pytest.fixture
def app(database_settings: DatabaseSettings) -> Litestar:
    return create_app(database_settings, verifier=DevTokenVerifier({TEST_TOKEN: TEST_IDENTITY}))


@pytest.fixture
def app_client(app: Litestar) -> Iterator[TestClient[Litestar]]:
    """Cliente já autenticado: os testes de negócio não repetem o token."""
    with TestClient(app=app) as client:
        client.headers["Authorization"] = f"Bearer {TEST_TOKEN}"
        yield client


@pytest.fixture
def rodar_com_sessao(
    database_settings: DatabaseSettings,
) -> Callable[[Callable[[AsyncSession], Awaitable[Any]]], Any]:
    """Roda um trecho async com sessão de banco própria, sem passar pela app.

    Serve pro que não tem rota de escrita de propósito — carteira e extrato só são gravados por
    job. Mesmo estilo síncrono (`asyncio.run`) do resto da suíte.
    """

    def _rodar(corpo: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
        async def principal() -> Any:
            config = create_sqlalchemy_config(database_settings)
            try:
                async with config.get_engine().begin() as conexao:
                    await conexao.run_sync(orm_registry.metadata.create_all)
                with use_identity(SYSTEM):
                    async with config.get_session() as sessao:
                        return await corpo(sessao)
            finally:
                await config.get_engine().dispose()

        return asyncio.run(principal())

    return _rodar


@pytest.fixture
def create_instrument(app_client: TestClient[Litestar]) -> Callable[..., dict[str, Any]]:
    def _create(**overrides: str) -> dict[str, Any]:
        payload = {"name": "caneta azul", "cetip_code": "CANE4", "instrument_type": "CRI"}
        response = app_client.post("/api/v1/ativos", data=payload | overrides)
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def post_trade(app_client: TestClient[Litestar]) -> Callable[..., httpx.Response]:
    def _post(instrument_id: int, **overrides: Any) -> httpx.Response:
        payload = {
            "fund_cnpj": FUND_CNPJ,
            "instrument_id": instrument_id,
            "trade_date": "2026-10-01",
            "side": "BUY",
            "quantity": 100,
            "unit_price": "101.25",
        }
        return app_client.post("/api/v1/boletas", json=payload | overrides)

    return _post
