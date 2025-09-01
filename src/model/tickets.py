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

    criado_em = fields.DatetimeField(default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))
    atualizado_em = fields.DatetimeField(default_factory=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))

    # 🔹 Relacionamento com usuário (empresa)
    usuario: fields.ForeignKeyRelation["Usuario"] = fields.ForeignKeyField(
        "models.Usuario", related_name="tickets"
    )
