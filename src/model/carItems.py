from sqlmodel import SQLModel, Field
from typing import Optional


class CartItem(SQLModel, table=True):
    """
    Representa um item do carrinho de compras.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int  # ID do usuário dono do carrinho
    product_id: int  # ID do produto
    product_name: str  # Nome do produto
    quantity: int  # Quantidade adicionada ao carrinho
    price: float  # Preço unitário do produto
    total_price: float  # Preço total (price * quantity - desconto + acréscimo)
    discount: Optional[float] = Field(default=0.0)  # desconto aplicado (R$)
    addition: Optional[float] = Field(default=0.0)  # acréscimo aplicado (R$)
    sale_code: Optional[str] = Field(
        default=None, max_length=6
    )  # Código da venda quando finalizada
