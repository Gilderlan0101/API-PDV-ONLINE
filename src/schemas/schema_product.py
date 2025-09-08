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

    BEVERAGES = 'Bebidas'
    FOODS = 'Alimentos'
    FRUITS = 'Frutas'
    VEGETABLES = 'Verduras'
    MEATS = 'Carnes'
    FISH = 'Peixes'
    DAIRY = 'Laticínios'
    BAKERY = 'Padaria'
    SWEETS = 'Doces'
    SNACKS = 'Salgados'
    HYGIENE = 'Higiene'
    CLEANING = 'Limpeza'
    CLOTHES = 'Roupas'
    SHOES = 'Calçados'
    ACCESSORIES = 'Acessórios'
    ELECTRONICS = 'Eletrônicos'
    HOME_APPLIANCES = 'Eletrodomésticos'
    TOOLS = 'Ferramentas'
    SCHOOL_SUPPLIES = 'Material escolar'
    FURNITURE = 'Móveis'
    TOYS = 'Brinquedos'
    GARDENING = 'Jardinagem'
    PETSHOP = 'Petshop'
    OTHERS = 'Outros'


# 🔹 Subgroups
class BeveragesSubGroup(str, Enum):
    REFRIGERANTES = "Refrigerantes"
    SUCOS = "Sucos"
    AGUA = "Água"
    ENERGETICOS = "Energéticos"
    CERVEJAS = "Cervejas"
    VINHOS = "Vinhos"
    CAFE_CHA = "Café e Chá"


class FoodsSubGroup(str, Enum):
    MASSAS = "Massas"
    ARROZ_FEIJAO = "Arroz e Feijão"
    ENLATADOS = "Enlatados"
    TEMPEROS = "Temperos e Condimentos"
    CONGELADOS = "Congelados"


class FruitsSubGroup(str, Enum):
    TROPICAIS = "Tropicais"
    CITRICAS = "Cítricas"
    VERMELHAS = "Frutas Vermelhas"
    SECAS = "Frutas Secas"


class VegetablesSubGroup(str, Enum):
    FOLHOSAS = "Folhosas"
    RAIZES = "Raízes"
    LEGUMES = "Legumes"
    BROTOS = "Brotos e Germinados"


class MeatsSubGroup(str, Enum):
    BOVINAS = "Bovinas"
    SUINAS = "Suínas"
    AVES = "Aves"
    EMBUTIDOS = "Embutidos"


class FishSubGroup(str, Enum):
    FRESCOS = "Peixes Frescos"
    CONGELADOS = "Peixes Congelados"
    FRUTOS_DO_MAR = "Frutos do Mar"


class DairySubGroup(str, Enum):
    LEITES = "Leites e Bebidas Lácteas"
    QUEIJOS = "Queijos"
    IOGURTES = "Iogurtes"
    MANTEIGAS = "Manteigas e Cremes"


class BakerySubGroup(str, Enum):
    PAES = "Pães"
    BOLOS = "Bolos"
    TORTAS = "Tortas"
    SALGADOS_ASSADOS = "Salgados Assados"


class SweetsSubGroup(str, Enum):
    CHOCOLATES = "Chocolates"
    BALAS = "Balas e Confeitos"
    SORVETES = "Sorvetes"
    BOLACHAS = "Bolachas"


class SnacksSubGroup(str, Enum):
    CHIPS = "Chips"
    PIPOCAS = "Pipocas"
    SNACKS_SAUDAVEIS = "Snacks Saudáveis"
    PETISCOS = "Petiscos"


# Adicione os subgrupos restantes da mesma forma, se necessário...


# ======================================
# 🔹 Units
# ======================================
class UnitOfMeasurement(str, Enum):
    """Unit of measurement for products"""

    UNIT = 'Unidade'
    KG = 'Kilograma (kg)'
    GRAM = 'Grama (g)'
    LITER = 'Litro (l)'
    ML = 'Mililitro (ml)'
    MILHEIRO = 'Milheiro'
    CAIXA = 'Caixa'
    PACOTE = 'Pacote'
    PAR = 'Par'
    ROLO = 'Rolo'
    SACO = 'Saco'
    FARDO = 'Fardo'
    BARRA = 'Barra'
    POTE = 'Pote'
    FRASCO = 'Frasco'
    VIDRO = 'Vidro'
    UNIDADE_CAIXA = 'Unidade em Caixa'


# ======================================
# 🔹 Product Status / Type
# ======================================
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


class TicketType(str, Enum):
    """Types of sales tickets"""

    NEW = "Novo"
    PROMOTION = "Promoção"
    COMBO = "Combo"
    BEST_SELLER = "Mais Vendido"
    SPECIAL_OFFER = "Oferta Especial"
    SEASONAL = "Sazonal"
    LIMITED = "Edição Limitada"


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

    name: Str150
    product_code: Str50
    stock: NonNegativeInt
    stoke_min: NonNegativeInt
    stoke_max: NonNegativeInt
    date_expired: Optional[datetime] = None
    fabricator: Optional[str] = None
    cost_price: NonNegativeFloat
    price_uni: NonNegativeFloat
    sale_price: NonNegativeFloat
    supplier: Optional[str] = None
    lot_bar_code: Optional[str] = None
    image_url: Optional[str] = None

    # 🔹 Connected enums and options
    product_type: ProductType
    active: ProductStatus
    group: str  # Optional[str] = None
    sub_group: str  # Optional[str] = None
    sector: str  # ProductSector
    unit: str  # Optional[str] = None
    controllstoke: ProductStatus
    sales_config: Optional[ApplyingSalesType] = None


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
    product_type: Optional[str] = None
    active: Optional[ProductStatus] = None
    group: Optional[str] = None
    sub_group: Optional[str] = None  # Novo campo de subgrupo
    sector: Optional[str] = None
    unit: Optional[str] = None
    controllstoke: Optional[str] = None
    sales_config: Optional[str] = None
