from datetime import datetime, timedelta
from typing import Annotated, List, Optional
from zoneinfo import ZoneInfo

from pydantic import EmailStr, constr
from sqlmodel import Field, Relationship, SQLModel

# ========================
# 🔹 Tipos Pydantic para validação
# ========================
UsernameType = Annotated[str, constr(min_length=3, max_length=50)]
CompanyNameType = Annotated[str, constr(min_length=3, max_length=100)]
PasswordType = Annotated[str, constr(min_length=8)]
CpfCnpjType = Annotated[str, constr(min_length=11, max_length=14)]  # 11=CPF, 14=CNPJ


# ========================
# 🔹 Usuário
# ========================
class Usuario(SQLModel, table=True):
    """Representa um usuário do sistema PDV vinculado a uma empresa."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Dados do usuário
    username: str = Field(index=True, unique=True, max_length=50)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    foto_perfil: Optional[str] = Field(
        default=None, description='URL ou caminho da foto de perfil'
    )

    # Dados da empresa
    company_name: str = Field(index=True, description='Razão Social')
    trade_name: Optional[str] = Field(default=None, description='Nome Fantasia')
    membros: int = Field(default=1, description='Quantidade de filiais do usuário')

    # Inscrições fiscais
    cpf: Optional[str] = Field(default=None, index=True, unique=True)
    cnpj: Optional[str] = Field(default=None, index=True, unique=True)
    state_registration: Optional[str] = Field(
        default=None, description='Inscrição Estadual'
    )
    municipal_registration: Optional[str] = Field(
        default=None, description='Inscrição Municipal'
    )
    cnae_principal: Optional[str] = Field(default=None, description='CNAE principal')
    crt: Optional[int] = Field(
        default=None, description='Código de regime tributário (1,2,3)'
    )

    # Endereço da empresa
    cep: Optional[str] = Field(default=None, description='CEP')
    street: Optional[str] = Field(default=None, description='Logradouro')
    number: Optional[str] = Field(default=None, description='Número')
    complement: Optional[str] = Field(default=None, description='Complemento')
    district: Optional[str] = Field(default=None, description='Bairro')
    city: Optional[str] = Field(default=None, description='Cidade')
    state: Optional[str] = Field(default=None, description='UF')

    # Auditoria
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    atualizado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    # Relacionamentos principais
    membros_filiais: List['Membro'] = Relationship(back_populates='usuario')
    cnpj_cache: List['CNPJCache'] = Relationship(back_populates='usuario')
    produtos: List['Produto'] = Relationship(back_populates='usuario')
    produtos_arquivados: List['ProdutoArquivado'] = Relationship(
        back_populates='usuario'
    )
    vendas: List['Sales'] = Relationship(back_populates='usuario')


# ========================
# 🔹 Membro / Filial
# ========================
class Membro(SQLModel, table=True):
    """Representa uma filial vinculada a um usuário principal."""

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str = Field(index=True, description='Nome da filial')
    cpf: Optional[str] = Field(default=None, index=True, unique=True)
    cnpj: Optional[str] = Field(default=None, index=True, unique=True)
    gerente: str = Field(description='Nome do gerente responsável')

    # Relacionamento com usuário
    usuario_id: int = Field(foreign_key='usuario.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='membros_filiais')

    # Auditoria
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    atualizado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )


# ========================
# 🔹 Cache de CNPJ
# ========================
class CNPJCache(SQLModel, table=True):
    """Cache de consultas de CNPJ para evitar excesso de chamadas na API."""

    id: Optional[int] = Field(default=None, primary_key=True)
    cnpj: str = Field(index=True, unique=True)
    data_json: str
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    usuario_id: Optional[int] = Field(foreign_key='usuario.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='cnpj_cache')

    def is_valid(self, ttl_minutes: int = 8) -> bool:
        """Valida se o cache ainda é válido baseado no TTL."""
        return datetime.now(
            ZoneInfo('America/Sao_Paulo')
        ) - self.updated_at < timedelta(minutes=ttl_minutes)


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

    usuario_id: int = Field(foreign_key='usuario.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='produtos')


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
    usuario_id: int = Field(foreign_key='usuario.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='produtos_arquivados')

    # FK opcional para histórico do produto original
    produto_id: Optional[int] = Field(default=None, foreign_key='produto.id')


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

    # Relacionamento com o usuário
    usuario_id: int = Field(foreign_key='usuario.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='vendas')
