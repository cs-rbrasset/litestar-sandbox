import datetime
from typing import Annotated

from litestar import Controller, get
from litestar.di import Provide
from litestar.params import FromQuery, QueryParameter

from modules.extrato.deps import ExtratoServiceDep, provide_extrato_service
from modules.extrato.schemas import ExtratoResposta, LancamentoResposta

FundoCnpjQuery = Annotated[str, QueryParameter(pattern=r"^\d{14}$")]


class ExtratoController(Controller):
    path = "/extratos"
    dependencies = {"extrato_service": Provide(provide_extrato_service)}

    @get()
    async def consultar(
        self,
        extrato_service: ExtratoServiceDep,
        fundo_cnpj: FundoCnpjQuery,
        data_referencia: FromQuery[datetime.date],
    ) -> ExtratoResposta:
        lancamentos = await extrato_service.lancamentos_em(fundo_cnpj, data_referencia)
        return ExtratoResposta(
            fundo_cnpj=fundo_cnpj,
            data_referencia=data_referencia,
            lancamentos=[
                LancamentoResposta(
                    documento=lancamento.documento,
                    tipo=lancamento.tipo,
                    descricao=lancamento.descricao,
                    valor=lancamento.valor,
                    referencia_origem=lancamento.referencia_origem,
                )
                for lancamento in lancamentos
            ],
        )
