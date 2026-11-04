from pathlib import Path

from litestar_vite import PathConfig, ViteConfig, VitePlugin

# backend/api/core/vite.py -> raiz do repositório
WEB_DIR = Path(__file__).resolve().parents[3] / "frontend"


def create_vite_plugin() -> VitePlugin:
    """litestar-vite só pra CLI (`litestar assets ...`), sem efeito em runtime.

    mode="framework": quem possui dev server, build e deploy é o SvelteKit, não o
    Litestar — mesmo princípio do exemplo oficial sveltekit/ do litestar-vite, mas sem o
    proxy SSR dele (hooks.server.ts): web-svelte-kit é SPA pura falando com a API via
    CORS, não SSR. enabled=False mantém a API pura: nenhuma rota, middleware, proxy ou
    lifespan é registrado em runtime, só os comandos `litestar assets
    build/serve/doctor/generate-types` ficam disponíveis, apontados pro projeto certo.
    """
    return VitePlugin(
        ViteConfig(
            mode="framework",
            enabled=False,
            paths=PathConfig(root=WEB_DIR),
        )
    )
