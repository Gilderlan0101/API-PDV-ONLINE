from typing import Optional
from unittest.mock import Base
from pydantic import BaseModel, EmailStr, model_validator
from sqlmodel import Field

"""
Shema_user.py: Onde criamos validações de login e cadastro
do usuario.
"""


class LoginSchema(BaseModel):
    email: EmailStr
    pwd: str


class CompanyRegisterSchema(BaseModel):
    # Dados pessoais
    full_name: str
    cpf: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    pwd: str

    # Dados da empresa
    cnpj: Optional[str] = None
    company_name: str
    trade_name: Optional[str] = None
    state_registration: Optional[str] = None
    municipal_registration: Optional[str] = None
    cnae_principal: Optional[str] = None
    crt: Optional[int] = None  # 1, 2 ou 3

    # Endereço
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

    # Devemos cria verificaçoes de cpf e cnpj aqui
    def verify_document(self):
        pass

    @model_validator(mode='before')
    def check_cpf_or_cnpj(cls, values):
        if not values.get('cpf') and not values.get('cnpj'):
            raise ValueError('Informe pelo menos CPF ou CNPJ.')
        return values


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'  # padrão para OAuth2
