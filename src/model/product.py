from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel


# Relações


# ========================
# 🔹 Produto
# ========================
class Produto(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_code: str = Field(index=True, max_length=50)
    name: str = Field(index=True, max_length=150)
    stock: int = Field(default=0)
    stoke_min: int = Field(default=0)
    stoke_max: int = Field(default=0)
    date_expired: Optional[datetime] = None
    fabricator: Optional[str] = None
    cost_price: float
    price_uni: float
    sale_price: float
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[str] = None

    # 🔹 Campos extras do schema
    product_type: Optional[str] = None
    active: Optional[str] = None
    group: Optional[str] = None
    sub_group: Optional[str] = None
    sector: Optional[str] = None
    unit: Optional[str] = None
    controllstoke: Optional[str] = None
    sales_config: Optional[str] = None  # Pode salvar JSON

    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    atualizado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    usuario_id: int = Field(foreign_key='usuarios.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='produtos')  # type: ignore
    # 🔹 Relação com fornecedor
    fornecedor_id: Optional[int] = Field(default=None, foreign_key='fornecedor.id')
    fornecedor: Optional['Fornecedor'] = Relationship(back_populates='produtos')
    


# ========================
# 🔹 Produto Arquivado
# ========================
class ProdutoArquivado(SQLModel, table=True):
    """Produto arquivado para histórico e relatórios."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Copia os dados do produto
    product_code: str = Field(index=True, max_length=50)
    name: str = Field(index=True, max_length=150)
    stock: int = Field(default=0)
    date_expired: Optional[datetime] = None
    fabricator: Optional[str] = None
    cost_price: float
    price_uni: float
    sale_price: float
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[str] = None

    # Motivo do arquivamento
    description: str = Field(
        ...,
        description='Motivo do arquivamento (ex: vendido, danificado, removido)',
    )

    # Auditoria
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    atualizado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    # Relacionamentos
    usuario_id: int = Field(foreign_key='usuarios.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='produtos_arquivados')  # type: ignore

    # FK opcional para histórico do produto original
    produto_id: Optional[int] = Field(default=None, foreign_key='produto.id')
