from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel


# ========================
# 🔹 Funcionário (Employees)
# ========================
class Employees(SQLModel, table=True):
    """Funcionários do PDV vinculados a um usuário (empresa)."""

    __tablename__ = "employees"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(index=True, max_length=150)
    cargo: Optional[str] = Field(default=None, max_length=100)
    email: str = Field(default=None, max_length=150)
    senha: str = Field(default=None, max_length=4)
    telefone: Optional[str] = Field(default=None, max_length=20)
    ativo: bool = Field(default=True)

    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo"))
    )

    # 🔹 Relacionamento com o usuário (empresa)
    usuario_id: int = Field(foreign_key="usuarios.id")

    usuario: Optional["Usuario"] = Relationship(back_populates="funcionarios")  # type: ignore

    # 🔹 Relacionamento com vendas feitas pelo funcionário
    vendas: List["Sales"] = Relationship(back_populates="funcionario")  # type: ignore
