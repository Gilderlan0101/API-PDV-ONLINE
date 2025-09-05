from enum import Enum
from pydantic import BaseModel, confloat, field_validator, Field, validator
from typing import Optional
from datetime import date, datetime
from pydantic_br import CPF, CEP
import re


# ------------------------------
# Enum de status do cliente
# ------------------------------
class Status(Enum):
    """Status do cliente: ATIVO, PENDENTE, ATRASO. Relacionado a fatura"""

    ATIVO = 'ATIVO'
    PENDENTE = 'PENDENTE'
    ATRASO = 'ATRASO'


# ------------------------------
# Schema para exibir clientes
# ------------------------------
class GetCustomers(BaseModel):
    full_name: str
    cpf: str
    credit: float  # Crédito total disponível
    current_balance: float  # Saldo atual disponível
    total_spent: float  # Gasto total acumulado (novo campo)
    due_date: datetime
    status: str

    class Config:
        from_attributes = True

    def model_dump_br(self):
        data = self.model_dump()
        # Formata crédito como valor monetário brasileiro
        data['credit'] = f"R$ {data['credit']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        # Formata data
        data['due_date'] = data['due_date'].strftime('%d/%m/%Y')
        return data

    def flag_status(self):
        # Aqui comparamos due_date com ela mesma para teste
        if self.due_date.date() == self.due_date.date():
            return Status.ATRASO
        return self.status


# ------------------------------
# Schema para cadastro de clientes
# ------------------------------
class SchemasCustomer(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Nome completo do cliente")
    birth_date: datetime
    cpf: CPF
    mother_name: Optional[str] = Field(None, max_length=150)
    road: str = Field(..., max_length=150)
    house_number: int
    neighborhood: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)
    tel: str
    cep: CEP
    credit: confloat(ge=0)  # agora aceita decimais >=0
    due_date: datetime
    status: Status

    # Validação de datas
    @field_validator('birth_date', 'due_date', mode='before')
    def parse_date(cls, v):
        if isinstance(v, str):
            if '/' in v:
                day, month, year = map(int, v.split('/'))
                if year < 100:
                    year += 2000 if year <= 30 else 1900
                return datetime(year, month, day)
            elif '-' in v and len(v) == 10:
                return datetime.strptime(v, '%Y-%m-%d')
        return v

    # Validação de telefone
    @field_validator('tel')
    def validate_tel(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) not in [10, 11]:
            raise ValueError("Telefone inválido. Deve ter 10 ou 11 dígitos (com DDD).")
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:]}" if len(digits) == 11 else f"({digits[0:2]}) {digits[2:6]}-{digits[6:]}"

    # Formatação de CPF e CEP
    # @field_validator('cpf', 'cep', mode='before')
    # def format_br_fields(cls, v, info):
    #     digits = re.sub(r'\D', '', str(v))
    #     if info.field_name == 'cpf':
    #         if len(digits) != 14:
    #             raise ValueError("CPF inválido. Deve ter 11 dígitos.")
    #         return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    #     if info.field_name == 'cep':
    #         if len(digits) != 8:
    #             raise ValueError("CEP inválido. Deve ter 8 dígitos.")
    #         return f"{digits[0:5]}-{digits[5:]}"
    #     return v

    # Exibição em formato brasileiro
    def model_dump_br(self):
        data = self.model_dump()
        data['birth_date'] = data['birth_date'].strftime('%d/%m/%Y')
        data['due_date'] = data['due_date'].strftime('%d/%m/%Y')
        data['credit'] = f"R$ {data['credit']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return data

    class Config:
        json_encoders = {datetime: lambda v: v.strftime('%d/%m/%Y')}
        error_msg_templates = {
            'value_error.any_str.min_length': 'O campo {loc} deve ter no mínimo {limit_value} caracteres.',
            'value_error.any_str.max_length': 'O campo {loc} deve ter no máximo {limit_value} caracteres.',
            'value_error.number.not_ge': 'O campo {loc} deve ser maior ou igual a {limit_value}.',
            'type_error.integer': 'O campo {loc} deve ser um número inteiro válido.',
        }


# ------------------------------
# Schema para atualização de clientes (opcional)
# ------------------------------
class SchemasCustomerUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    birth_date: Optional[datetime] = None
    cpf: Optional[CPF] = None
    mother_name: Optional[str] = None
    road: Optional[str] = None
    house_number: Optional[int] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    tel: Optional[str] = None
    cep: Optional[CEP] = None
    credit: Optional[confloat(ge=0)] = None
    due_date: Optional[datetime] = None
    status: Optional[Status] = None

    @field_validator('birth_date', 'due_date', mode='before')
    def parse_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            if '/' in v:
                day, month, year = map(int, v.split('/'))
                if year < 100:
                    year += 2000 if year <= 30 else 1900
                return datetime(year, month, day)
            elif '-' in v and len(v) == 10:
                return datetime.strptime(v, '%Y-%m-%d')
        return v

    @field_validator('tel')
    def validate_tel(cls, v):
        if v is None:
            return v
        digits = re.sub(r'\D', '', v)
        if len(digits) not in [10, 11]:
            raise ValueError("Telefone inválido. Deve ter 10 ou 11 dígitos (com DDD).")
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:]}" if len(digits) == 11 else f"({digits[0:2]}) {digits[2:6]}-{digits[6:]}"

    # @field_validator('cpf', 'cep', mode='before')
    # def format_br_fields(cls, v, info):
    #     if v is None: return v
    #     digits = re.sub(r'\D', '', str(v))
    #     if info.field_name == 'cpf':
    #         if len(digits) != 11:
    #             raise ValueError("CPF inválido. Deve ter 11 dígitos.")
    #         return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    #     if info.field_name == 'cep':
    #         if len(digits) != 8:
    #             raise ValueError("CEP inválido. Deve ter 8 dígitos.")
    #         return f"{digits[0:5]}-{digits[5:]}"
    #     return v


# ------------------------------
# Schema de atualização de crédito
# ------------------------------
class SchemasCustomerCreditUpdate(BaseModel):
    current_balance: confloat(ge=0.0)  # saldo atual >= 0

    @field_validator('current_balance')
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError('Saldo não pode ser negativo')
        return v
