from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Annotated
from datetime import date, datetime
from pydantic import HttpUrl
from datetime import date

# Pydantic v2 recomendado com Annotated | Evitando erros de entrada de dados
Str50 = Annotated[str, Field(min_length=1, max_length=50)]
Str150 = Annotated[str, Field(min_length=2, max_length=150)]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class ProductRegisterSchema(BaseModel):
    product_code: Str50
    name: Str150
    stock: NonNegativeInt
    date_expired: Optional[datetime] = None  # 🔹 já compatível com o banco
    fabricator: Optional[str] = None
    cost_price: NonNegativeFloat
    price_uni: NonNegativeFloat
    sale_price: NonNegativeFloat
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[str] = None         # 🔹 agora é str direto


class ProductUpdateSchema(BaseModel):
    product_code: Optional[str] = None
    name: Optional[str] = None
    stock: Optional[int] = None
    date_expired: Optional[date] = None
    fabricator: Optional[str] = None
    cost_price: Optional[float] = None
    price_uni: Optional[float] = None
    sale_price: Optional[float] = None
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[HttpUrl] = None
