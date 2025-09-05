from datetime import datetime
from zoneinfo import ZoneInfo
from tortoise import fields, models
from typing import Optional

from src.model.product import Produto, ProdutoArquivado
from src.model.customers import Customer
from src.model.fornecedor import Fornecedor
from src.model.employee import Employees
from src.model.membros import Membro
from src.model.cnpjCache import CNPJCache


class Usuario(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=150)
    email = fields.CharField(max_length=200)
    password = fields.CharField(min_length=4, max_length=100)
    foto_perfil = fields.CharField(max_length=255, null=True, default=None)

    company_name = fields.CharField(max_length=100)
    trade_name = fields.CharField(max_length=100, null=True, default=None)
    membros = fields.IntField(null=True, default=0)

    cpf = fields.CharField(max_length=30, null=True, unique=True, default=None)
    cnpj = fields.CharField(max_length=30, null=True, unique=True, default=None)
    state_registration = fields.CharField(max_length=50, default="Valor não informado")
    municipal_registration = fields.CharField(max_length=120, default="Valor não informado")
    cnae_principal = fields.CharField(max_length=120, null=True, default=None)
    crt = fields.CharField(max_length=120, null=True, default=None)

    cep = fields.CharField(max_length=20, default="Valor não informado")
    street = fields.CharField(max_length=60, default="Valor não informado")
    home_number = fields.CharField(max_length=20, default="Valor não informado")
    complement = fields.CharField(max_length=60, default="Valor não informado")
    district = fields.CharField(max_length=50, default="Valor não informado")
    city = fields.CharField(max_length=100, default="Valor não informado")
    state = fields.CharField(max_length=50, default="Valor não informado")

    criado_em = fields.DatetimeField(default=datetime.now(ZoneInfo('America/Sao_Paulo')))
    atualizado_em = fields.DatetimeField(default=datetime.now(ZoneInfo('America/Sao_Paulo')))

    # 🔹 Relações
    membros_filiais = fields.ReverseRelation["Membro"]
    cnpj_cache = fields.ReverseRelation["CNPJCache"]
    produtos = fields.ReverseRelation["Produto"]
    produtos_arquivados = fields.ReverseRelation["ProdutoArquivado"]
    employees = fields.ReverseRelation["Employees"]
    fornecedores = fields.ReverseRelation["Fornecedor"]
    customers = fields.ReverseRelation["Customer"]
