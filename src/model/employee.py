from tortoise import models, fields
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from src.model.caixa import Caixa
from src.model.customers import Sales


class Employees(models.Model):
    """
    Funcionários do PDV vinculados a um usuário (empresa).
    """

    id = fields.IntField(pk=True)
    nome = fields.CharField(max_length=150, index=True)
    cargo = fields.CharField(max_length=100, null=True)
    email = fields.CharField(max_length=150, null=True)
    senha = fields.CharField(max_length=90, null=True)
    result_of_all_sales = fields.IntField(default=0, null=True)
    telefone = fields.CharField(max_length=20, null=True)
    ativo = fields.BooleanField(default=True)
    criado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    # 🔹 Relacionamento com o usuário (empresa)
    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="funcionarios",
        null=True,
        on_delete=fields.SET_NULL,
    )

    # 🔹 Relacionamento com vendas feitas pelo funcionário
    # Relacionamento reverso (precisa do modelo Sales)
    vendas: fields.ReverseRelation["Sales"]

    # 🔹 Relacionamento com caixas abertos por esse funcionário
    # Relacionamento reverso (precisa do modelo Caixa)
    caixas: fields.ReverseRelation["Caixa"]

    class Meta:
        table = "employees"
