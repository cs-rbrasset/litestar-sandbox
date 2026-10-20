# web/: página de visualização da POC

Uma página HTML com [HTMX](https://htmx.org/) para clicar no fluxo da POC (ativos → boletas → liquidação → posições). Não faz parte da aplicação nem do exercício: é só uma forma de ver a API funcionando.

## Como rodar

Em dois terminais:

```bash
# 1. a API
uv run litestar --app litestar_sandbox.app:create_app run

# 2. a página (serve web/ e repassa /api para a API)
uv run python web/serve.py
```

Abra <http://127.0.0.1:5500>.

## Como funciona

- A API responde JSON, e o HTMX espera HTML. A extensão `client-side-templates` transforma o JSON em HTML no navegador, com os templates Mustache que estão no fim do `index.html`.
- O `serve.py` (só biblioteca padrão) serve a página e repassa tudo o que começa com `/api` para a API. Com a página e a API na mesma origem, o navegador não bloqueia as chamadas por CORS, e a aplicação não precisa mudar.
- Os formulários de ativos vão como form-urlencoded (o que o `POST /instruments` espera), e os de boletas vão como JSON, com a extensão `json-enc`.
- Os erros da API (`400`, `404`, `409`) aparecem como mensagens no canto da tela, com o `detail` e as mensagens por campo.

Variáveis opcionais: `API_URL` (padrão `http://127.0.0.1:8000`) e `WEB_PORT` (padrão `5500`).
