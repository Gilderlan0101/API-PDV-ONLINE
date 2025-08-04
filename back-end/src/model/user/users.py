from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel import SQLModel, Field
from pydantic import EmailStr, constr
from typing import Annotated, List, Optional


# Validando os campos antes de entroduzir a class
# Tipos validados | usuario
UsernameType = Annotated[str, constr(min_length=3, max_length=50)]
CompanyNameType = Annotated[str, constr(min_length=3, max_length=100)]
PasswordType = Annotated[str, constr(min_length=8)]
CpfCnpjType = Annotated[
    str, constr(min_length=11, max_length=14)
]  # 11 para CPF, 14 para CNPJ


class Usuario(SQLModel, table=True):
    """
    Representa um usuário do sistema PDV vinculado a uma empresa.
    """

    id: int | None = Field(default=None, primary_key=True)

    # Dados do usuário
    username: str = Field(index=True, unique=True, max_length=50)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    foto_perfil: Optional[str] = Field(
        default=None, description='URL ou caminho da foto de perfil'
    )

    # Dados da empresa
    company_name: str = Field(index=True, description='Razão Social')
    trade_name: Optional[str] = Field(
        default=None, description='Nome Fantasia'
    )
    membros: int = Field(
        default=1, description='Quantidade de lojas ou filiais do usuário'
    )

    # Inscrições fiscais
    cpf: Optional[str] = Field(default=None, index=True, unique=True)
    cnpj: Optional[str] = Field(default=None, index=True, unique=True)
    state_registration: Optional[str] = Field(
        default=None, description='Inscrição Estadual'
    )
    municipal_registration: Optional[str] = Field(
        default=None, description='Inscrição Municipal'
    )
    cnae_principal: Optional[str] = Field(
        default=None, description='CNAE principal'
    )
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

    # Relacionamento reverso: lista de membros/filiais
    membro: List['Membro'] = Relationship(back_populates='usuario')


class Membro(SQLModel, table=True):
    """
    Representa uma loja ou filial vinculada a um usuário principal.
    """

    id: int | None = Field(default=None, primary_key=True)

    # Dados da filial/membro
    nome: str = Field(index=True, description='Nome da filial ou membro')
    cpf: Optional[str] = Field(default=None, index=True, unique=True)
    cnpj: Optional[str] = Field(default=None, index=True, unique=True)
    gerente: str = Field(description='Nome do gerente responsável')

    # Relacionamento com Usuario
    usuario_id: int = Field(
        foreign_key='usuario.id'
    )  # FK para a tabela Usuario

    # Auditoria
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    atualizado_em: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo('America/Sao_Paulo'))
    )
    usuario: Optional['Usuario'] = Relationship(back_populates='membro')
