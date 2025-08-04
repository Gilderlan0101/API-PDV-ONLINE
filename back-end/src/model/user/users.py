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
    username: UsernameType = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: PasswordType
    foto_perfil: str | None = Field(
        default=None, description='URL ou caminho da foto de perfil'
    )

    # Dados da empresa
    company_name: CompanyNameType = Field(index=True)
    membros: int = Field(
        default=1, description='Quantidade de lojas ou filiais do usuário'
    )

    # CPF ou CNPJ (apenas um deve ser usado)
    cpf: str | None = Field(default=None, index=True, unique=True)
    cnpj: str | None = Field(default=None, index=True, unique=True)

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
