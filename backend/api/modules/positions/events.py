"""Evento que desacopla o controller de relatórios do Prefect.

O controller não conhece mais `recompute_positions_report`: só publica
`PositionsReportRequested` e espera o `future` que o listener (listeners.py) resolve com o
`task_run_id`. Mesma forma de desacoplamento que `trades.public.TradeSettled` já usa entre
módulos — aqui é dentro do próprio `positions`, mas o motivo é o mesmo: quem dispara o evento
não precisa saber como (nem com o quê) ele é tratado.
"""

import asyncio
import datetime

import msgspec

POSITIONS_REPORT_REQUESTED = "positions.report_requested"


class PositionsReportRequested(msgspec.Struct, frozen=True):
    fund_cnpj: str
    reference_dates: list[datetime.date]
    # o listener roda em background (SimpleEventEmitter não espera o handler); é o future, não
    # o retorno do listener, que devolve o task_run_id pro controller que publicou o evento.
    future: asyncio.Future[str]


__all__ = ("POSITIONS_REPORT_REQUESTED", "PositionsReportRequested")
