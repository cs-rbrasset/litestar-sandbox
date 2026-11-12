"""Processo dos jobs **em dev**, ao lado do `app.py` — a outra metade do backend.

Descobre os jobs de `modules/*/tasks.py`, registra um deployment `<job>/padrao` pra cada um no
server local e executa os runs neste processo — do mesmo jeito que o `app.py` deixa o autowire
descobrir os controllers: nenhum módulo é citado aqui. Não existe app Litestar neste processo —
job não publica evento (ver `core/jobs.py`).

    uv run --env-file ../../.env python worker.py

Produção não usa este arquivo: os jobs são publicados no servidor Prefect da RBR pelo
`implantar.py` e carregados de `fluxos.py` dentro de um container.
"""

from core.jobs import servir

if __name__ == "__main__":
    servir()
