from tortoise.models import Model
from tortoise import fields

class CartItem(Model):
    """ CarItem é responsável por guardar compras do cliente temporariamente. """

    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=False)
    product_id = fields.IntField(null=False)
    product_name = fields.TextField(null=False)
    quantity = fields.IntField(null=False)
    price = fields.FloatField(null=False)
    price_total = fields.FloatField(null=False, default=0.0)  # ⚡ Corrigido
    discount = fields.FloatField(null=True)
    addition = fields.FloatField(null=True)
    product_code = fields.TextField(null=True)
