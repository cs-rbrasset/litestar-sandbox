"""Processo do worker de jobs, ao lado do `app.py` — a outra metade do backend.

Descobre os jobs de `modules/*/tasks.py` e os serve, do mesmo jeito que o `app.py` deixa o
autowire descobrir os controllers: nenhum módulo é citado aqui. Não existe app Litestar neste
processo — job não publica evento (ver `core/jobs.py`).

    uv run --env-file ../../.env python worker.py
"""

from core.jobs import servir

if __name__ == "__main__":
    servir()
