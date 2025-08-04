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


class RegistreSchema(BaseModel):
    full_name: str
    email: EmailStr
    company_name: str
    pwd: str
    cpf: Optional[str] = None
    cnpj: Optional[str] = None

    @model_validator(mode='before')
    def check_cpf_or_cnpj(cls, values):
        if not values.get('cpf') and not values.get('cnpj'):
            raise ValueError('Informe pelo menos CPF ou CNPJ.')
        return values
