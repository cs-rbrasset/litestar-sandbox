"""Porta de object storage: arquivo gerado ou recebido nunca mora no banco nem no disco.

Quatro operações e nada mais (`put`, `get`, `list`, `url_assinada`) — a porta vaza o
vocabulário de armazenamento de objetos de propósito, mas só o que é realmente usado. Quem
chama não sabe qual provedor está atrás.

Credencial de serviço própria, separada da do banco, e **nunca** chega ao front: o acesso a um
objeto é sempre por URL assinada de validade curta, nunca por bucket público.

Adaptadores:
  - `ArmazenamentoSupabase` — o que está em uso hoje (API REST do Storage).
  - `ArmazenamentoEmMemoria` — testes; nada de I/O.
  - `ArmazenamentoS3` — [AJUSTAR: qual object storage] stub pra MinIO/S3 (dev local com MinIO).
"""

import os
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import niquests

from core.settings import SupabaseSettings

if TYPE_CHECKING:
    from collections.abc import Iterable

# o default do niquests (5s) já estourou uma vez num upload real; a API do Storage é externa
_TIMEOUT = 30.0


class ObjetoNaoEncontradoError(LookupError):
    """Caminho inexistente no bucket."""


@runtime_checkable
class Armazenamento(Protocol):
    """Porta usada por módulos e jobs — a implementação concreta vem do `core`."""

    async def put(self, caminho: str, conteudo: bytes, tipo: str) -> None: ...

    async def get(self, caminho: str) -> bytes: ...

    async def list(self, prefixo: str) -> list[str]: ...

    async def url_assinada(self, caminho: str, expira_em: int = 3600) -> str: ...


class ArmazenamentoSupabase:
    """Supabase Storage via API REST — não é a conexão do Postgres (`DatabaseSettings`)."""

    def __init__(self, settings: SupabaseSettings) -> None:
        self._settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        chave = self._settings.service_role_key
        return {"Authorization": f"Bearer {chave}", "apikey": chave}

    def _url(self, acao: str, sufixo: str = "") -> str:
        return f"{self._settings.url}/storage/v1/{acao}/{self._settings.bucket}{sufixo}"

    async def put(self, caminho: str, conteudo: bytes, tipo: str) -> None:
        headers = self._headers | {"Content-Type": tipo, "x-upsert": "true"}
        async with niquests.AsyncSession(timeout=_TIMEOUT) as sessao:
            resposta = await sessao.post(self._url("object", f"/{caminho}"), headers=headers, data=conteudo)
            resposta.raise_for_status()

    async def get(self, caminho: str) -> bytes:
        async with niquests.AsyncSession(timeout=_TIMEOUT) as sessao:
            resposta = await sessao.get(self._url("object", f"/{caminho}"), headers=self._headers)
            if resposta.status_code == 404:
                raise ObjetoNaoEncontradoError(caminho)
            resposta.raise_for_status()
            return resposta.content or b""

    async def list(self, prefixo: str) -> list[str]:
        corpo = {"prefix": prefixo, "limit": 1000}
        async with niquests.AsyncSession(timeout=_TIMEOUT) as sessao:
            resposta = await sessao.post(self._url("object/list"), headers=self._headers, json=corpo)
            resposta.raise_for_status()
            itens = resposta.json() or []
        return [f"{prefixo.rstrip('/')}/{item['name']}" for item in itens]

    async def url_assinada(self, caminho: str, expira_em: int = 3600) -> str:
        async with niquests.AsyncSession(timeout=_TIMEOUT) as sessao:
            resposta = await sessao.post(
                self._url("object/sign", f"/{caminho}"),
                headers=self._headers,
                json={"expiresIn": expira_em},
            )
            resposta.raise_for_status()
            assinado = resposta.json()["signedURL"]
        return f"{self._settings.url}/storage/v1{assinado}"


class ArmazenamentoEmMemoria:
    """Storage dos testes: mesma porta, zero I/O. A URL assinada é falsa de propósito."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    async def put(self, caminho: str, conteudo: bytes, tipo: str) -> None:
        del tipo  # irrelevante em memória; faz parte da porta por causa do HTTP real
        self.objetos[caminho] = conteudo

    async def get(self, caminho: str) -> bytes:
        try:
            return self.objetos[caminho]
        except KeyError as erro:
            raise ObjetoNaoEncontradoError(caminho) from erro

    async def list(self, prefixo: str) -> list[str]:
        return sorted(c for c in self.objetos if c.startswith(prefixo))

    async def url_assinada(self, caminho: str, expira_em: int = 3600) -> str:
        if caminho not in self.objetos:
            raise ObjetoNaoEncontradoError(caminho)
        return f"memoria://{caminho}?expira_em={expira_em}"


class ArmazenamentoS3:
    """[AJUSTAR: qual object storage] — stub pra S3/MinIO.

    Dev local com MinIO, produção com o provedor escolhido; a credencial e o `endpoint_url`
    entram em `core/settings.py` junto. Falta escolher o cliente (`aiobotocore`/`aioboto3`) —
    decisão de dependência, não de arquitetura, por isso o stub falha alto em vez de fingir.
    """

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        msg = "[AJUSTAR] adaptador S3/MinIO ainda não implementado"
        raise NotImplementedError(msg)


def armazenamento_padrao() -> Armazenamento:
    """Adaptador configurado por ambiente — `STORAGE_BACKEND=memoria` nos testes."""
    escolha = os.getenv("STORAGE_BACKEND", "supabase").lower()
    if escolha == "memoria":
        return ArmazenamentoEmMemoria()
    if escolha == "s3":
        return ArmazenamentoS3()
    return ArmazenamentoSupabase(SupabaseSettings.from_env())


def juntar(*partes: str) -> str:
    """Caminho de objeto: sempre `/`, sem barra dupla e sem barra à esquerda."""
    return "/".join(parte.strip("/") for parte in partes if parte.strip("/"))


def como_prefixo(partes: Iterable[str]) -> str:
    return juntar(*partes) + "/"


__all__ = (
    "Armazenamento",
    "ArmazenamentoEmMemoria",
    "ArmazenamentoS3",
    "ArmazenamentoSupabase",
    "ObjetoNaoEncontradoError",
    "armazenamento_padrao",
    "como_prefixo",
    "juntar",
)
