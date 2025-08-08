from datetime import date, datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field, HttpUrl

# ======================================
# 🔹 Type Aliases for Validation
# ======================================
Str50 = Annotated[str, Field(min_length=1, max_length=50)]
Str150 = Annotated[str, Field(min_length=2, max_length=150)]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


# ======================================
# 🔹 Product Enums
# ======================================
class ProductGroup(str, Enum):
    """Main product categories"""

    BEVERAGES = 'bebidas'
    FOODS = 'alimentos'
    FRUITS = 'frutas'
    VEGETABLES = 'verduras'
    MEATS = 'carnes'
    FISH = 'peixes'
    DAIRY = 'laticínios'
    BAKERY = 'padaria'
    SWEETS = 'doces'
    SNACKS = 'salgados'
    HYGIENE = 'higiene'
    CLEANING = 'limpeza'
    CLOTHES = 'roupas'
    SHOES = 'calçados'
    ACCESSORIES = 'acessórios'
    ELECTRONICS = 'eletrônicos'
    HOME_APPLIANCES = 'eletrodomésticos'
    TOOLS = 'ferramentas'
    SCHOOL_SUPPLIES = 'material escolar'
    FURNITURE = 'móveis'
    TOYS = 'brinquedos'
    GARDENING = 'jardinagem'
    PETSHOP = 'petshop'
    OTHERS = 'outros'


class ProductSector(str, Enum):
    """Defines product origin"""

    LOCAL = 'Fabricação Própria'
    RESALE = 'Revenda'


class ProductStatus(str, Enum):
    """Defines if product is active or used in flags"""

    YES = 'Sim'
    NO = 'Não'


class ProductType(str, Enum):
    """Defines the type of product"""

    COMMON = 'Comum'
    FRACTIONAL = 'Fracionado'
    ADDITIONAL = 'Adicional'
    EDITABLE_VALUE = 'Valor editável'
    RAW_MATERIAL = 'Matéria prima'


class UnitOfMeasurement(str, Enum):
    """Unit of measurement for products"""

    UNIT = 'UNIDADE'
    KG = 'KG'
    MILHEIRO = 'MILHEIRO'


class TicketType(str, Enum):
    """Types of sales tickets"""

    TICKET_1 = 'Ticket 1'
    TICKET_2 = 'Ticket 2'
    TICKET_3 = 'Ticket 3'
    TICKET_4 = 'Ticket 4'


class ApplyingSalesType(BaseModel):
    """Optional sales application settings for a product"""

    discount: Optional[ProductStatus] = None
    rate: Optional[ProductStatus] = None
    balance: Optional[ProductStatus] = None
    valid: Optional[str] = None
    ticket: Optional[TicketType] = None


# ======================================
# 🔹 Product Schemas
# ======================================
class ProductRegisterSchema(BaseModel):
    """Schema for registering a new product"""

    product_code: Str50
    name: Str150
    stock: NonNegativeInt
    stoke_min: NonNegativeInt
    stoke_max: NonNegativeInt
    date_expired: Optional[datetime] = None  # Compatible with DB
    fabricator: Optional[str] = None
    cost_price: NonNegativeFloat
    price_uni: NonNegativeFloat
    sale_price: NonNegativeFloat
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[str] = None

    # 🔹 Connected enums and options
    product_type: ProductType  # Product type
    active: ProductStatus  # Product active status
    group: ProductGroup  # Product category
    sector: ProductSector  # Product sector
    unit: UnitOfMeasurement  # Unit of measurement
    controllstoke: ProductStatus  # Stock control
    sales_config: Optional[ApplyingSalesType] = None  # Sales behavior


class ProductUpdateSchema(BaseModel):
    """Schema for updating product information"""

    product_code: Optional[str] = None
    name: Optional[str] = None
    stock: Optional[int] = None
    stoke_min: Optional[int] = None
    stoke_max: Optional[int] = None
    date_expired: Optional[date] = None
    fabricator: Optional[str] = None
    cost_price: Optional[float] = None
    price_uni: Optional[float] = None
    sale_price: Optional[float] = None
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    description: Optional[str] = None

    # 🔹 Connected enums and options
    product_type: Optional[ProductType] = None
    active: Optional[ProductStatus] = None
    group: Optional[ProductGroup] = None
    sector: Optional[ProductSector] = None
    unit: Optional[UnitOfMeasurement] = None
    controllstoke: Optional[ProductStatus] = None
    sales_config: Optional[ApplyingSalesType] = None
