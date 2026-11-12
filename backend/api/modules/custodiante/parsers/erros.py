"""Erros de parse: são erros de **domínio**, não de coleta.

Repetir um job que falhou aqui não melhora nada — o arquivo é o mesmo. Por isso entram no
`nao_repetir` do `@job` (ver `custodiante/tasks.py`): retry é só pra falha de coleta.
"""


class LayoutNaoReconhecidoError(ValueError):
    """O arquivo não tem a forma que esse parser espera (campo faltando, raiz errada...)."""


__all__ = ("LayoutNaoReconhecidoError",)
