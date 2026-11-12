"""A publicação dos jobs (`implantar.py`) — o que dá pra provar sem o servidor da RBR.

O `.deploy()` em si fala com GitHub e com o servidor Prefect; o que se trava aqui é o que ele
carrega: nenhum valor de ambiente em texto, e cada job com um entrypoint que existe.
"""

from pathlib import Path

import implantar
from core.jobs import descobrir, nome_no_entrypoint


def test_ambiente_dos_jobs_so_tem_referencias() -> None:
    """Valor literal ficaria gravado no deployment e visível na UI do Prefect."""
    for env, valor in implantar.ambiente_dos_jobs().items():
        assert valor.startswith("{{ prefect.blocks.secret.") or valor.startswith(
            "{{ prefect.variables."
        ), env


def test_credenciais_sao_blocos_secret() -> None:
    ambiente = implantar.ambiente_dos_jobs()
    for env in ("DATABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "CUSTODIANTE_BTG_TOKEN"):
        assert ambiente[env].startswith("{{ prefect.blocks.secret."), env


def test_resultado_do_job_vai_pra_storage_remoto() -> None:
    """A API lê o retorno do job (`status`); o container que o produziu já morreu."""
    assert "PREFECT_RESULTS_DEFAULT_STORAGE_BLOCK" in implantar.ambiente_dos_jobs()


def test_tag_do_job_e_o_modulo_dono() -> None:
    assert implantar.modulo_do_job("modules.custodiante.tasks") == "custodiante"


def test_entrypoint_e_relativo_a_raiz_do_clone() -> None:
    """O clone é do repositório inteiro: o caminho parte da raiz, não de `backend/api`."""
    import fluxos  # noqa: PLC0415

    raiz = Path(implantar.__file__).resolve().parents[2]
    assert (raiz / implantar.ENTRYPOINT).resolve() == Path(fluxos.__file__).resolve()
    for job in descobrir():
        # deployment sem atributo correspondente só quebraria no run, já em produção
        assert getattr(fluxos, nome_no_entrypoint(job)) is job
