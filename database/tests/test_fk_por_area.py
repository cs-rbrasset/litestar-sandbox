"""As tabelas deste pacote são contrato público: FK nunca cruza área.

O import-linter fiscaliza os imports entre módulos da API; isto fiscaliza o schema. Uma FK
entre áreas é o jeito mais fácil de acoplar dois domínios sem ninguém perceber — e o mais caro
de desfazer depois, porque já virou dado gravado.
"""

import importlib
import pkgutil

import database.models as pacote_models


def _tabelas_por_area() -> dict[str, str]:
    """`{nome da tabela: área}` — a área é o subpacote onde o model é declarado."""
    mapa: dict[str, str] = {}
    for info in pkgutil.iter_modules(pacote_models.__path__, f"{pacote_models.__name__}."):
        area = info.name.rsplit(".", 1)[-1]
        modulo = importlib.import_module(f"{info.name}.model")
        for valor in vars(modulo).values():
            tabela = getattr(valor, "__table__", None)
            if tabela is not None and getattr(valor, "__module__", "") == modulo.__name__:
                mapa[tabela.name] = area
    return mapa


def _metadados() -> set:
    metadados = set()
    for info in pkgutil.iter_modules(pacote_models.__path__, f"{pacote_models.__name__}."):
        modulo = importlib.import_module(f"{info.name}.model")
        for valor in vars(modulo).values():
            tabela = getattr(valor, "__table__", None)
            if tabela is not None:
                metadados.add(tabela.metadata)
    return metadados


def test_toda_tabela_mora_numa_area() -> None:
    areas = _tabelas_por_area()
    sem_area = [
        tabela.name
        for metadata in _metadados()
        for tabela in metadata.tables.values()
        if tabela.name not in areas
    ]
    assert not sem_area, f"tabelas declaradas fora de uma área: {sem_area}"


def test_sem_fk_entre_areas() -> None:
    areas = _tabelas_por_area()
    violacoes = [
        f"{tabela.name}.{fk.parent.name} -> {fk.column.table.name} "
        f"({areas[tabela.name]} -> {areas[fk.column.table.name]})"
        for metadata in _metadados()
        for tabela in metadata.tables.values()
        for fk in tabela.foreign_keys
        if tabela.name in areas
        and fk.column.table.name in areas
        and areas[tabela.name] != areas[fk.column.table.name]
    ]
    assert not violacoes, "FK cruzando área: " + "; ".join(violacoes)
