from datetime import datetime
from zoneinfo import ZoneInfo
from tortoise.models import Model
from tortoise import fields
from src.model.user import Usuario


class Ticket(Model):
    """
    Modelo de Tickets vinculado a um usuário (empresa).
    """

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=150)
    description = fields.TextField(null=True)

    # 🔹 CORREÇÃO: Use auto_now_add para criado_em e auto_now para atualizado_em
    criado_em = fields.DatetimeField(auto_now_add=True)
    atualizado_em = fields.DatetimeField(auto_now=True)

    # 🔹 Relacionamento com usuário (empresa)
    usuario: fields.ForeignKeyRelation["Usuario"] = fields.ForeignKeyField("models.Usuario", related_name="tickets")

    class Meta:
        table = "ticket"
