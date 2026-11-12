"""A borda HTTP do `custodiante`: controller → service → porta de jobs.

O dublê troca `enfileirar`/`status` — a fronteira que o módulo realmente conhece. Se alguém
voltar a importar o orquestrador dentro do módulo, estes testes continuam verdes e quem acusa é
o `lint-imports`.
"""

import datetime
import uuid
from typing import TYPE_CHECKING, Any

import pytest

from core.jobs import EstadoJob, ExecucaoNaoEncontradaError, OrquestradorIndisponivelError
from modules.custodiante import services as custodiante_services

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.testing import TestClient

FUNDO = "12345678000190"


@pytest.fixture
def fake_enfileirar(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    chamadas: dict[str, Any] = {"id_execucao": str(uuid.uuid4())}

    async def _enfileirar(job: Any, **parametros: Any) -> str:
        chamadas["job"] = job.name
        chamadas["parametros"] = parametros
        return chamadas["id_execucao"]

    monkeypatch.setattr(custodiante_services, "enfileirar", _enfileirar)
    return chamadas


def test_solicitar_importacao_enfileira_o_job_certo(
    app_client: TestClient[Litestar], fake_enfileirar: dict[str, Any]
) -> None:
    resposta = app_client.post(
        "/api/v1/custodiantes/importacoes",
        json={
            "codigo": "btg",
            "documento": "carteira",
            "fundo_cnpj": FUNDO,
            "data": "2026-10-31",
        },
    )

    assert resposta.status_code == 202, resposta.text
    assert resposta.json() == {"id_execucao": fake_enfileirar["id_execucao"]}
    assert fake_enfileirar["job"] == "custodiante-importar-carteira"
    assert fake_enfileirar["parametros"] == {
        "codigo": "btg",
        "fundo_cnpj": FUNDO,
        "data": datetime.date(2026, 10, 31),
    }


def test_reprocessamento_enfileira_o_job_de_reprocessar(
    app_client: TestClient[Litestar], fake_enfileirar: dict[str, Any]
) -> None:
    resposta = app_client.post(
        "/api/v1/custodiantes/reprocessamentos",
        json={"documento": "carteira", "prefixo": "custodiante/btg/carteira/x", "forcar": True},
    )

    assert resposta.status_code == 202, resposta.text
    assert fake_enfileirar["job"] == "custodiante-reprocessar-carteira"
    assert fake_enfileirar["parametros"] == {
        "prefixo": "custodiante/btg/carteira/x",
        "forcar": True,
    }


def test_custodiante_fora_do_registro_e_400(app_client: TestClient[Litestar]) -> None:
    resposta = app_client.post(
        "/api/v1/custodiantes/importacoes",
        json={
            "codigo": "nao_existe",
            "documento": "carteira",
            "fundo_cnpj": FUNDO,
            "data": "2026-10-31",
        },
    )

    assert resposta.status_code == 400, resposta.text


def test_cnpj_fora_do_formato_e_400(app_client: TestClient[Litestar]) -> None:
    resposta = app_client.post(
        "/api/v1/custodiantes/importacoes",
        json={"codigo": "btg", "documento": "carteira", "fundo_cnpj": "123", "data": "2026-10-31"},
    )

    assert resposta.status_code == 400, resposta.text


def test_orquestrador_fora_do_ar_e_503(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _indisponivel(job: Any, **parametros: Any) -> str:
        raise OrquestradorIndisponivelError("connection refused")

    monkeypatch.setattr(custodiante_services, "enfileirar", _indisponivel)

    resposta = app_client.post(
        "/api/v1/custodiantes/importacoes",
        json={
            "codigo": "btg",
            "documento": "carteira",
            "fundo_cnpj": FUNDO,
            "data": "2026-10-31",
        },
    )

    assert resposta.status_code == 503, resposta.text


def test_consulta_devolve_a_referencia_de_origem_quando_terminou(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _status(id_execucao: str) -> EstadoJob:
        return EstadoJob(
            id=id_execucao,
            estado="COMPLETED",
            concluido=True,
            resultado="custodiante/btg/carteira/x",
        )

    monkeypatch.setattr(custodiante_services, "status", _status)

    resposta = app_client.get("/api/v1/custodiantes/importacoes/abc")

    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {
        "id_execucao": "abc",
        "estado": "COMPLETED",
        "concluido": True,
        "referencia_origem": "custodiante/btg/carteira/x",
    }


def test_consulta_de_execucao_inexistente_e_404(
    app_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _status(id_execucao: str) -> EstadoJob:
        raise ExecucaoNaoEncontradaError(id_execucao)

    monkeypatch.setattr(custodiante_services, "status", _status)

    resposta = app_client.get("/api/v1/custodiantes/importacoes/nao-existe")

    assert resposta.status_code == 404, resposta.text
