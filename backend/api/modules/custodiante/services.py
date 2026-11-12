"""Regra de aplicação do `custodiante`: traduzir um pedido HTTP em job enfileirado.

Sem banco: este módulo não tem tabela. O estado da execução mora no orquestrador, atrás de
`core.jobs.status` — não existe tabela de "importações" aqui, de propósito.
"""


from typing import TYPE_CHECKING

from core.jobs import EstadoJob, enfileirar, status
from modules.custodiante.enums import CodigoCustodiante, TipoDocumento
from modules.custodiante.registro import CustodianteDesconhecidoError, registrado
from modules.custodiante.tasks import (
    importar_carteira,
    importar_extrato,
    reprocessar_carteira,
    reprocessar_extrato,
)

if TYPE_CHECKING:
    import datetime

_IMPORTAR = {
    TipoDocumento.CARTEIRA: importar_carteira,
    TipoDocumento.EXTRATO: importar_extrato,
}
_REPROCESSAR = {
    TipoDocumento.CARTEIRA: reprocessar_carteira,
    TipoDocumento.EXTRATO: reprocessar_extrato,
}


class ImportacaoService:
    async def solicitar_importacao(
        self,
        codigo: CodigoCustodiante,
        documento: TipoDocumento,
        fundo_cnpj: str,
        data: datetime.date,
    ) -> str:
        """Devolve o id da execução na hora. Valida o código aqui pra falhar em 400, não no job.

        Só a existência no registro: montar o gateway exigiria credencial, e credencial é
        problema do worker, não de quem pede a importação.
        """
        if not registrado(codigo):
            raise CustodianteDesconhecidoError(codigo)
        return await enfileirar(
            _IMPORTAR[documento], codigo=codigo.value, fundo_cnpj=fundo_cnpj, data=data
        )

    async def solicitar_reprocessamento(
        self, documento: TipoDocumento, prefixo: str, *, forcar: bool = False
    ) -> str:
        return await enfileirar(_REPROCESSAR[documento], prefixo=prefixo, forcar=forcar)

    async def consultar(self, id_execucao: str) -> EstadoJob:
        return await status(id_execucao)
