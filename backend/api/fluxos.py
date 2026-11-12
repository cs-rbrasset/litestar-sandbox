"""Entrypoint dos jobs em produção — o arquivo que o Prefect carrega dentro do container.

Por que existe: em produção o run clona o repositório inteiro e carrega o entrypoint **a partir
da raiz do clone**. O Prefect põe no `sys.path` a pasta do arquivo de entrypoint e a raiz — não
`backend/api`. Apontar o deployment direto pra `modules/x/tasks.py` quebraria no primeiro
`from core... import`. Este arquivo mora em `backend/api/` justamente pra que a pasta dele seja
a que entra no `sys.path`.

Expõe cada job descoberto como atributo de módulo (`custodiante_importar_carteira`...), com o
nome vindo de `core.jobs.nome_no_entrypoint` — o mesmo que o `implantar.py` grava no
deployment. Nenhum módulo é citado aqui: job novo aparece sozinho, igual no `worker.py`.

`database/src` entra no `sys.path` pelo mesmo motivo: na imagem de jobs só estão as
dependências de terceiros; o código do repositório (API e `database`) vem sempre do clone, na
mesma versão.

Em dev, este arquivo não é usado: `worker.py` → `core.jobs.servir()`.
"""

import sys
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
for _caminho in (_AQUI, _AQUI.parents[1] / "database" / "src"):
    if str(_caminho) not in sys.path:
        sys.path.insert(0, str(_caminho))

from core.jobs import descobrir, nome_no_entrypoint  # noqa: E402 — depende do sys.path acima

globals().update({nome_no_entrypoint(j): j for j in descobrir()})
