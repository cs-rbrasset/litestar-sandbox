"""Valores aceitos nas colunas de `carteira` — tuplas de texto, não `Enum`.

A fonte de verdade do vocabulário é o modelo canônico, em
`backend/api/modules/carteira/domain/canonico.py`. Aqui vai uma cópia deliberada: `database`
não pode importar `backend/api` (a dependência é num sentido só) e o domínio não pode importar
`database` (regra de pureza). A divergência entre os dois é pega por teste
(`backend/api/tests/modules/carteira/test_vocabulario_sincronizado.py`), não por revisão.
"""

CLASSES_ATIVO: tuple[str, ...] = (
    "titulo_publico",
    "titulo_privado",
    "compromissada",
    "cota",
    "derivativo",
    "provisao",
    "caixa",
    "outro",
)

__all__ = ("CLASSES_ATIVO",)
