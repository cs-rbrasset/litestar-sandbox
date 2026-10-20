"""Servidor de desenvolvimento da página de visualização.

Serve os arquivos desta pasta e repassa tudo o que começa com /api para a API
Litestar. Assim a página e a API ficam na mesma origem e o navegador não
bloqueia as chamadas por CORS, sem precisar mudar nada na aplicação.

Uso (com a API rodando em outro terminal):
    uv run python web/serve.py              # página em http://127.0.0.1:5500
    API_URL=http://127.0.0.1:8001 uv run python web/serve.py
"""

import http.server
import os
import urllib.error
import urllib.request
from pathlib import Path

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
PORT = int(os.getenv("WEB_PORT", "5500"))
WEB_DIR = Path(__file__).parent

# Cabeçalhos que não devem ser repassados entre as duas conexões.
HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "content-length", "host"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        request = urllib.request.Request(
            API_URL + self.path, data=body, headers=headers, method=self.command
        )
        try:
            with urllib.request.urlopen(request) as response:  # noqa: S310 (URL local fixa)
                status, resp_headers, payload = response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            status, resp_headers, payload = error.code, error.headers, error.read()
        except urllib.error.URLError:
            status, resp_headers = 502, {}
            payload = b'{"detail": "API fora do ar. Suba a API antes (veja web/README.md)."}'
            resp_headers = {"Content-Type": "application/json"}

        self.send_response(status)
        for key, value in resp_headers.items():
            if key.lower() not in HOP_BY_HOP:
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _route(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy()
        elif self.command == "GET":
            super().do_GET()
        else:
            self.send_error(405)

    do_GET = do_POST = do_PATCH = do_DELETE = _route  # noqa: N815


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Página: http://127.0.0.1:{PORT}  (repassando /api para {API_URL})")  # noqa: T201
    server.serve_forever()
