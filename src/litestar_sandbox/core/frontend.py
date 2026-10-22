from pathlib import Path

from litestar_vite import ViteConfig, VitePlugin
from litestar_vite.config import PathConfig, RuntimeConfig, TypeGenConfig

# src/litestar_sandbox/core/frontend.py -> raiz do repositório
WEB_DIR = Path(__file__).resolve().parents[3] / "web"


def create_vite_plugin(api_prefix: str) -> VitePlugin:
    """SPA em Vite servida pela própria API.

    Em dev (VITE_DEV_MODE=true) o Litestar sobe o dev server do Vite e faz o proxy do HMR
    pela mesma porta; em produção serve o build de web/public a partir do manifest.
    """
    return VitePlugin(
        ViteConfig(
            mode="spa",
            paths=PathConfig(root=WEB_DIR, resource_dir="src", bundle_dir="public"),
            # sem isso, um /api/... inexistente cai no fallback da SPA e responde 200 com HTML
            runtime=RuntimeConfig(extra_route_prefixes=(api_prefix,)),
            types=TypeGenConfig(output=WEB_DIR / "src" / "generated"),
        )
    )
