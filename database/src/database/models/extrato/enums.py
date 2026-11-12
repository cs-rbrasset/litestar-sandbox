"""Valores aceitos nas colunas de `extrato` — mesma cópia deliberada de `carteira/enums.py`.

Fonte de verdade: `backend/api/modules/extrato/domain/canonico.py`. A divergência é pega por
teste (`backend/api/tests/modules/extrato/test_vocabulario_sincronizado.py`).
"""

TIPOS_LANCAMENTO: tuple[str, ...] = (
    "aplicacao",
    "resgate",
    "liquidacao",
    "tarifa",
    "rendimento",
    "transferencia",
    "outro",
)

__all__ = ("TIPOS_LANCAMENTO",)
