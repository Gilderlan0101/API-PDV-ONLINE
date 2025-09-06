from tortoise import fields, models
from datetime import datetime
from zoneinfo import ZoneInfo


class Sales(models.Model):
    """
    Modelo de vendas do PDV.
    Cada venda está vinculada a um usuário (empresa),
    pode ou não ter um funcionário associado,
    e deve sempre estar ligada a um produto.
    """

    id = fields.IntField(pk=True)
    product_name = fields.CharField(max_length=150)
    quantity = fields.IntField(default=1)
    total_price = fields.FloatField()
    lucro_total = fields.FloatField(default=0.0)
    cost_price = fields.FloatField()
    sale_code = fields.CharField(max_length=6, null=True, index=True)

    criado_em = fields.DatetimeField(auto_now_add=True)

    # 🔹 Relacionamento com o usuário (empresa dono da venda)
    usuario = fields.ForeignKeyField("models.Usuario", related_name="vendas", on_delete=fields.CASCADE)

    # 🔹 Relacionamento com o funcionário operador (opcional)
    funcionario = fields.ForeignKeyField("models.Employees", related_name="vendas", null=True, on_delete=fields.SET_NULL)

    # 🔹 Relacionamento com o produto (obrigatório)
    produto = fields.ForeignKeyField(
        "models.Produto",
        related_name="vendas",
        null=False,
        on_delete=fields.RESTRICT,  # impede apagar produto se houver vendas
    )
    
    

    class Meta:
        table = "sales"
        ordering = ["-criado_em"]
