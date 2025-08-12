from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel

# Relações
from src.model.user import Usuario
from src.model.employee import Employees
from src.model.product import Produto


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
    usuario_id: int = Field(foreign_key="usuario.id")
    usuario: Optional["Usuario"] = Relationship(back_populates="vendas")

    # 🔹 Relacionamento com o funcionário que fez a venda
    funcionario_id: Optional[int] = Field(foreign_key="employees.id")
    funcionario: Optional["Employees"] = Relationship(back_populates="vendas")

    # 🔹 Relacionamento com o produto vendido
    produto_id: Optional[int] = Field(foreign_key="produto.id")
    produto: Optional["Produto"] = Relationship()
