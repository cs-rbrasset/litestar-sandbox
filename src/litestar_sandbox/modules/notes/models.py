from typing import Any

from advanced_alchemy.base import BigIntAuditBase
from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class Note(BigIntAuditBase):
    # várias por pessoa agora (artigos), não mais um notepad único: sem unique aqui.
    owner: Mapped[str] = mapped_column(String(70), index=True)
    title: Mapped[str] = mapped_column(String(200), default="Sem título")
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # copiado da Identity no save, não FK: nenhuma tabela de pessoas existe pra referenciar.
    author_name: Mapped[str] = mapped_column(String(200), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
