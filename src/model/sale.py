from tortoise import fields, models
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo



class Sales(models.Model):
    id = fields.IntField(pk=True)
    product_name = fields.CharField(max_length=150)
    quantity = fields.IntField(default=1)
    total_price = fields.FloatField()
    lucro_total = fields.FloatField(default=0.0)
    cost_price = fields.FloatField()
    codigo_da_venda = fields.CharField(max_length=6, null=True)
    criado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    # 🔹 Relacionamento com o usuário (empresa)
    usuario = fields.ForeignKeyField("models.Usuario", related_name="vendas", on_delete=fields.CASCADE)

    # 🔹 Relacionamento com o funcionário
    funcionario = fields.ForeignKeyField(
        "models.Employees", related_name="vendas", null=True, on_delete=fields.SET_NULL
    )

    # 🔹 Relacionamento com o produto
    produto = fields.ForeignKeyField(
        "models.Produto", related_name="vendas", null=True, on_delete=fields.SET_NULL
    )
