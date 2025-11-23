# src/model/cash_movement.py
from datetime import datetime
from zoneinfo import ZoneInfo

from tortoise import fields, models


class CashMovement(models.Model):
    """
    Registro de movimentações do caixa
    """

    id = fields.IntField(pk=True)
    # 'ENTRADA', 'SAIDA', 'ABERTURA', 'FECHAMENTO'
    tipo = fields.CharField(max_length=20)
    valor = fields.FloatField()
    descricao = fields.TextField()
    criado_em = fields.DatetimeField(
        default=datetime.now(ZoneInfo('America/Sao_Paulo'))
    )

    # Relacionamentos
    caixa = fields.ForeignKeyField(
        'models.Caixa', related_name='movimentacoes'
    )
    usuario = fields.ForeignKeyField(
        'models.Usuario', related_name='movimentacoes_caixa'
    )
    funcionario = fields.ForeignKeyField(
        'models.Employees', related_name='movimentacoes', null=True
    )
    venda = fields.ForeignKeyField(
        'models.Sales', related_name='movimentacoes', null=True
    )

    class Meta:
        table = 'cash_movements'
