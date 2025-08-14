from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel


# Tabela que registra no banco os produtos vendidos e lucro total
class Sales(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    product_name: str = Field(index=True, max_length=150)
    quantity: int = Field(default=1)
    total_price: float = Field()
    lucro_total: float = Field(default=0.0)
    cost_price: float

    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    # 🔹 Relacionamento com o usuário (empresa)
    usuario_id: int = Field(foreign_key="usuarios.id")  # type: ignore
    usuario: Optional["Usuario"] = Relationship(back_populates="vendas")  # type: ignore
    # 🔹 Relacionamento com o funcionário que fez a venda
    funcionario_id: Optional[int] = Field(
        default=None,
        foreign_key="employees.id",  # tem que bater com o nome da tabela no Employees
    )

    funcionario: Optional["Employees"] = Relationship(back_populates="vendas")  # type: ignore

    # 🔹 Relacionamento com o produto vendido
    produto_id: Optional[int] = Field(foreign_key="produto.id")
    codigo_da_venda: Optional[str] = Field(max_length=6)

    produto: Optional["Produto"] = Relationship()  # type: ignore
