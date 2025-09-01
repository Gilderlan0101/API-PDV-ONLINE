from tortoise import fields, models
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

class Membro(models.Model):
    id = fields.IntField(pk=True)
    nome = fields.CharField(max_length=150)
    cpf = fields.CharField(max_length=11, null=True, default=None)
    cnpj = fields.CharField(max_length=14, null=True, default=None)
    gerente = fields.CharField(max_length=100)

    criado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))
    atualizado_em = fields.DatetimeField(default=datetime.now(ZoneInfo("America/Sao_Paulo")))

    # 🔹 Relacionamento com o usuário dono do membro
    usuario = fields.ForeignKeyField(
        "models.Usuario", related_name="membros_filiais", null=False
    )
