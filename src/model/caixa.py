from tortoise import models, fields
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional


class Caixa(models.Model):
    """
    Modelo de Caixa vinculado a um usuário e a um funcionário.
    """

    id = fields.IntField(pk=True)
    nome = fields.CharField(max_length=100, default="Caixa Principal")
    saldo_inicial = fields.FloatField(default=0.0)  # Valor de abertura
    saldo_atual = fields.FloatField(default=0.0)  # Atualizado com vendas
    valor_fechamento = fields.FloatField(null=True)  # Valor informado ao fechar
    valor_sistema = fields.FloatField(null=True)  # Total do sistema calculado
    diferenca = fields.FloatField(null=True)  # Diferença entre valor_fechamento e valor_sistema
    aberto = fields.BooleanField(default=False)
    criado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))
    atualizado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    # # Colunas temporarias para gerenciamento do caiax
    # produto_nome = fields.TextField(null=True)
    # produto_id = fields.IntField(null=True)
    # quantidade = fields.IntField(default=0, null=True)

    valor_total = fields.FloatField(default=0.0)

    # 🔹 Relacionamentos
    usuario = fields.ForeignKeyField("models.Usuario", related_name="caixas", on_delete=fields.CASCADE)

    funcionario = fields.ForeignKeyField("models.Employees", related_name="caixas", null=True, on_delete=fields.SET_NULL)

    class Meta:
        table = "caixas"
