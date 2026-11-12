"""Publica os jobs no servidor Prefect da RBR, via `rbr-prefect` — um deployment por job.

Ferramenta de publicação, não código do app: roda na máquina de quem publica (ou num CI dentro
da rede da RBR), nunca na API nem no job. Por isso é o único arquivo, além de `core/jobs.py`,
que importa `prefect` — e o único que importa `rbr_prefect` (contrato do import-linter).

    cd backend/api
    JOBS_IMAGEM=10.214.20.79:5000/litestar-sandbox-jobs:<tag> \\
        uv run --group implantacao python implantar.py
    # sem terminal (agente/CI): acrescente --rbr-non-interactive

Ordem de uma publicação (ver `docs/playbook/` — capítulo de jobs):

    1. commit no main, com push      (o rbr-prefect recusa main sujo ou sem push)
    2. imagem de jobs, se o uv.lock mudou   (`Dockerfile.jobs`, na raiz)
    3. este script                    (deployments apontando pro commit atual)
    4. API                            (só então ela pode chamar um job novo ou alterado)

O que cada deployment carrega:

  - **código**: clone do GitHub **fixado no commit** de quem publica (`_FixadoNoCommit`), não
    o HEAD do branch — senão um push mudaria o que roda em produção sem publicar nada, e a API
    ficaria fora de sincronia com os jobs;
  - **imagem**: `JOBS_IMAGEM`, só com as dependências de terceiros (Python 3.14 — as imagens
    padrão da RBR são 3.12);
  - **entrypoint**: `backend/api/fluxos.py:<job>` (ver lá por que não aponta pro `tasks.py`);
  - **ambiente**: só referências — segredo vira bloco `Secret`, configuração vira variável do
    Prefect, ambos resolvidos pelo worker na hora do run. Nenhum valor passa por aqui, então
    nenhum valor fica gravado no deployment nem aparece na UI.

Pré-requisitos no servidor (uma vez, por quem administra): os blocos de `SEGREDOS`, as
variáveis de `VARIAVEIS` e o bloco de result storage que a variável
`litestar_sandbox_bloco_de_resultados` nomeia.
"""

import os
import subprocess
import sys

from prefect.runner.storage import GitRepository
from prefect_github import GitHubCredentials
from rbr_prefect import DefaultDeploy
from rbr_prefect.constants import RBRBlocks, RBRDependencyMode
from rbr_prefect.deploy import GitHubSourceStrategy

from core.jobs import NOME_DEPLOYMENT, descobrir, nome_no_entrypoint

ENTRYPOINT = "backend/api/fluxos.py"

#: variável de ambiente → bloco `Secret` do Prefect (slug). Credencial nunca em texto.
SEGREDOS = {
    "DATABASE_URL": "litestar-sandbox-database-url",
    "SUPABASE_SERVICE_ROLE_KEY": "litestar-sandbox-supabase-service-role-key",
    "CUSTODIANTE_BTG_TOKEN": "litestar-sandbox-custodiante-btg-token",
}

#: variável de ambiente → variável do Prefect. Configuração que não é segredo.
VARIAVEIS = {
    "DB_ASSUME_IDENTITY": "litestar_sandbox_db_assume_identity",
    "SUPABASE_URL": "litestar_sandbox_supabase_url",
    "SUPABASE_STORAGE_BUCKET": "litestar_sandbox_supabase_storage_bucket",
    "CUSTODIANTE_BTG_URL": "litestar_sandbox_custodiante_btg_url",
    # o retorno do job é lido pela API (`core.jobs.status`), não pelo container que o
    # produziu — e o container morre no fim do run. Sem storage remoto, não há resultado.
    "PREFECT_RESULTS_DEFAULT_STORAGE_BLOCK": "litestar_sandbox_bloco_de_resultados",
}


def ambiente_dos_jobs() -> dict[str, str]:
    """O `env` do container: só templates que o worker resolve na hora do run."""
    return {
        **{env: f"{{{{ prefect.blocks.secret.{bloco} }}}}" for env, bloco in SEGREDOS.items()},
        **{env: f"{{{{ prefect.variables.{nome} }}}}" for env, nome in VARIAVEIS.items()},
    }


def modulo_do_job(fn_module: str) -> str:
    """`modules.custodiante.tasks` → `custodiante`: a tag que agrupa os runs na UI."""
    return fn_module.split(".")[1]


class _FixadoNoCommit(GitHubSourceStrategy):
    """A estratégia do `rbr-prefect`, mas clonando um commit, não o HEAD do branch.

    URL, branch (pra descrição), entrypoint e os checks de git continuam os do pacote; só o
    `build()` muda. O `GitRepository` do Prefect não aceita branch e commit juntos.
    """

    def __init__(self, commit: str) -> None:
        super().__init__()
        self._commit = commit

    def build(self) -> GitRepository:
        return GitRepository(
            url=self._resolve_github_url(),
            commit_sha=self._commit,
            credentials=GitHubCredentials.load(RBRBlocks.GITHUB_CREDENTIALS),
            include_submodules=True,
        )


def _commit_atual() -> str:
    resultado = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607 — git do PATH, como o próprio rbr-prefect
        capture_output=True,
        text=True,
        check=True,
    )
    return resultado.stdout.strip()


def main() -> None:
    imagem = os.environ.get("JOBS_IMAGEM")
    if not imagem:
        sys.exit("JOBS_IMAGEM não definida (ex.: 10.214.20.79:5000/litestar-sandbox-jobs:<tag>)")

    jobs = descobrir()
    if not jobs:
        sys.exit("nenhum job encontrado em modules/*/tasks.py")

    commit = _commit_atual()
    ambiente = ambiente_dos_jobs()
    for job in jobs:
        DefaultDeploy(
            flow_func=job,
            name=NOME_DEPLOYMENT,
            tags=[modulo_do_job(job.fn.__module__)],
            source_strategy=_FixadoNoCommit(commit),
            entrypoint=f"{ENTRYPOINT}:{nome_no_entrypoint(job)}",
            image=imagem,
            # a imagem já traz as dependências; AUTO_INSTALL exigiria `[project]` na raiz do
            # repositório (é só workspace) e instalaria a cada run. PIP_PACKAGES sem
            # requirements detectados não injeta nada.
            dependency_mode=RBRDependencyMode.PIP_PACKAGES,
            extra_env=ambiente,
        ).deploy()


if __name__ == "__main__":
    main()
