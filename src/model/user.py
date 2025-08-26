from datetime import date, datetime, timedelta
from enum import Enum
from typing import Annotated, List, Optional
from zoneinfo import ZoneInfo
from pydantic import EmailStr, constr
from sqlmodel import JSON, Column, Field, Relationship, SQLModel, String, Text

# Relações


UsernameType = Annotated[str, constr(min_length=3, max_length=50)]
CompanyNameType = Annotated[str, constr(min_length=3, max_length=100)]
PasswordType = Annotated[str, constr(min_length=8)]
CpfCnpjType = Annotated[str, constr(min_length=11, max_length=14)]  # 11=CPF, 14=CNPJ


# ========================
# 🔹 Usuário
# ========================
class Usuario(SQLModel, table=True):
    """Representa um usuário do sistema PDV vinculado a uma empresa."""

    __tablename__ = 'usuarios'  # type: ignore

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
    produtos: List['Produto'] = Relationship(back_populates='usuario')  # type: ignore
    produtos_arquivados: List['ProdutoArquivado'] = Relationship(  # type: ignore
        back_populates='usuario'
    )  # type: ignore
    vendas: List['Sales'] = Relationship(back_populates='usuario')  # type: ignore
    funcionarios: List["Employees"] = Relationship(back_populates="usuario")  # type: ignore
    fornecedores: List['Fornecedor'] = Relationship(back_populates='usuario')
    tickets: List['Ticket'] = Relationship(back_populates='usuario')




class Ticket(SQLModel, table=True):
    """Representa um ticket/etiqueta de destaque para produtos do usuário"""

    __tablename__ = 'tickets'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, index=True, description="Nome do ticket")
    description: Optional[str] = Field(default=None, description="Descrição do ticket")
    
    # Auditoria
    criado_em: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))

    # Relacionamento com usuário
    usuario_id: int = Field(foreign_key='usuarios.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='tickets')


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
    usuario_id: int = Field(foreign_key='usuarios.id')
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

    usuario_id: Optional[int] = Field(foreign_key='usuarios.id')
    usuario: Optional['Usuario'] = Relationship(back_populates='cnpj_cache')

    def is_valid(self, ttl_minutes: int = 8) -> bool:
        """Valida se o cache ainda é válido baseado no TTL."""
        return datetime.now(
            ZoneInfo('America/Sao_Paulo')
        ) - self.updated_at < timedelta(minutes=ttl_minutes)
        


# =========================
# Enums
# =========================
class SupplierType(str, Enum):
    PESSOA_JURIDICA = "PJ"
    PESSOA_FISICA = "PF"

class TaxRegime(str, Enum):
    SIMPLES_NACIONAL = "Simples Nacional"
    LUCRO_PRESUMIDO = "Lucro Presumido"
    LUCRO_REAL = "Lucro Real"
    MEI = "MEI"
    OUTRO = "Outro"

class IEStatus(str, Enum):
    CONTRIBUINTE = "Contribuinte"
    ISENTO = "Isento"
    NAO_CONTRIBUINTE = "Não Contribuinte"

class PaymentTerm(str, Enum):
    AVISTA = "À vista"
    DIAS_7 = "7 dias"
    DIAS_14 = "14 dias"
    DIAS_21 = "21 dias"
    DIAS_28 = "28 dias"
    DIAS_30 = "30 dias"
    DIAS_45 = "45 dias"
    DIAS_60 = "60 dias"
    PERSONALIZADO = "Personalizado"

class SupplierStatus(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    BLOQUEADO = "Bloqueado"
    PENDENTE = "Pendente"
    
    
# =========================
# Modelo principal: Fornecedor
# =========================
class Fornecedor(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identificação
    tipo: SupplierType = Field(default=SupplierType.PESSOA_JURIDICA, index=True)
    razao_social: str = Field(sa_column=Column("razao_social", String(200), nullable=False))
    nome_fantasia: Optional[str] = Field(default=None, sa_column=Column(String(200)))

    # Documentos
    cnpj: Optional[str] = Field(default=None, sa_column=Column(String(14), unique=True, index=True))
    cpf: Optional[str] = Field(default=None, sa_column=Column(String(11), unique=True, index=True))
    ie_status: IEStatus = Field(default=IEStatus.CONTRIBUINTE)
    inscricao_estadual: Optional[str] = Field(default=None, sa_column=Column(String(20)))
    inscricao_municipal: Optional[str] = Field(default=None, sa_column=Column(String(20)))

    # Fiscal
    regime_tributario: TaxRegime = Field(default=TaxRegime.SIMPLES_NACIONAL)

    # Contatos
    email: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    telefones: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    site: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    contato_principal: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    contatos_secundarios: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))

    # Endereço
    endereco: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    # Financeiro
    prazo_pagamento: PaymentTerm = Field(default=PaymentTerm.DIAS_30)
    prazo_personalizado_dias: Optional[int] = None
    limite_credito: float = Field(default=0)
    desconto_padrao_percent: float = Field(default=0)

    # Bancário
    contas_bancarias: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))

    # Operacional
    categorias_fornecimento: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: SupplierStatus = Field(default=SupplierStatus.ATIVO)

    # Auditoria
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    ativo_desde: Optional[date] = None
    criado_por: Optional[str] = Field(default=None, sa_column=Column(String(100)))
    atualizado_por: Optional[str] = Field(default=None, sa_column=Column(String(100)))

    # Chave estrangeira para usuário
    usuario_id: int = Field(foreign_key="usuarios.id", nullable=False)
    usuario: Optional["Usuario"] = Relationship(back_populates="fornecedores")



