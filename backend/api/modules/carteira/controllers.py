import datetime
from typing import Annotated

from litestar import Controller, get
from litestar.di import Provide
from litestar.params import FromQuery, QueryParameter

from modules.carteira.deps import CarteiraServiceDep, provide_carteira_service
from modules.carteira.schemas import CarteiraResposta, PosicaoResposta

# restrição de query param vai no QueryParameter(...): msgspec.Meta é ignorado fora do body
FundoCnpjQuery = Annotated[str, QueryParameter(pattern=r"^\d{14}$")]


class CarteiraController(Controller):
    path = "/carteiras"
    dependencies = {"carteira_service": Provide(provide_carteira_service)}

    @get()
    async def consultar(
        self,
        carteira_service: CarteiraServiceDep,
        fundo_cnpj: FundoCnpjQuery,
        data_referencia: FromQuery[datetime.date],
    ) -> CarteiraResposta:
        posicoes = await carteira_service.posicoes_em(fundo_cnpj, data_referencia)
        return CarteiraResposta(
            fundo_cnpj=fundo_cnpj,
            data_referencia=data_referencia,
            posicoes=[
                PosicaoResposta(
                    classe=p.classe,
                    identificador=p.identificador,
                    descricao=p.descricao,
                    quantidade=p.quantidade,
                    valor=p.valor,
                    referencia_origem=p.referencia_origem,
                )
                for p in posicoes
            ],
        )
