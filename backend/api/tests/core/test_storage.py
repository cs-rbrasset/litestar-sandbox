"""A porta de storage pelo adaptador em memória — o mesmo contrato que o Supabase cumpre."""

import asyncio

import pytest

from core.storage import ArmazenamentoEmMemoria, ObjetoNaoEncontradoError, juntar


def test_juntar_normaliza_barras() -> None:
    assert juntar("custodiante/", "/btg", "carteira/") == "custodiante/btg/carteira"
    assert juntar("a", "", "b") == "a/b"


def test_grava_le_e_lista_por_prefixo() -> None:
    armazenamento = ArmazenamentoEmMemoria()

    async def corpo() -> list[str]:
        await armazenamento.put("p/a.xml", b"<a/>", "application/xml")
        await armazenamento.put("p/b.xml", b"<b/>", "application/xml")
        await armazenamento.put("outro/c.xml", b"<c/>", "application/xml")
        assert await armazenamento.get("p/a.xml") == b"<a/>"
        return await armazenamento.list("p/")

    assert asyncio.run(corpo()) == ["p/a.xml", "p/b.xml"]


def test_objeto_inexistente_levanta_erro_da_porta() -> None:
    armazenamento = ArmazenamentoEmMemoria()

    with pytest.raises(ObjetoNaoEncontradoError):
        asyncio.run(armazenamento.get("nao/existe"))


def test_url_assinada_exige_que_o_objeto_exista() -> None:
    """Bucket privado: não existe URL permanente nem pública pra objeto nenhum."""
    armazenamento = ArmazenamentoEmMemoria()

    with pytest.raises(ObjetoNaoEncontradoError):
        asyncio.run(armazenamento.url_assinada("nao/existe"))
