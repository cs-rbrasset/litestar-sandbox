from typing import TypeAlias

from litestar.di import NamedDependency
from litestar.params import SkipValidation

from modules.custodiante.services import ImportacaoService

ImportacaoServiceDep: TypeAlias = NamedDependency[SkipValidation[ImportacaoService]]


async def provide_importacao_service() -> ImportacaoService:
    """Sem sessão de banco: o módulo não tem tabela — quem grava é `carteira`/`extrato`."""
    return ImportacaoService()
