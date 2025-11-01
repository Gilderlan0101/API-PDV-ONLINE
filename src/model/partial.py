from tortoise import fields, models
from datetime import datetime
from zoneinfo import ZoneInfo


class Partial(models.Model):
    id = fields.IntField(pk=True)

    customers_name = fields.CharField(max_length=150, null=True)
    cpf = fields.CharField(max_length=90, null=False, unique=True)  # CPF como texto
    tel = fields.CharField(max_length=90, null=False, unique=True)  # Telefone como texto
    # product_name = fields.TextField(null=True)
    produto = fields.CharField(max_length=255, null=True)  # Adicione este campo
    value = fields.FloatField(null=True)
    payment_method = fields.CharField(max_length=15, null=True)
    date = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="partials",
        null=True,
    )


class finished_debts(models.Model):
    id = fields.IntField(pk=True)

    name = fields.CharField(max_length=150, null=True)
    tel = fields.CharField(max_length=90, null=True)
    product_name = fields.TextField(null=True)
    value = fields.FloatField(null=True)
    payments = fields.JSONField(null=True)
    date = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    usuario = fields.ForeignKeyField(
        "models.Usuario",
        related_name="patials_finished_debts",
        null=True,
    )
