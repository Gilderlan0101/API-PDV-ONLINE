from tortoise import fields, models
from datetime import datetime


class Delivery(models.Model):
    id = fields.IntField(pk=True)

    # 🔹 Relação com o dono da entrega (usuário da empresa)
    usuario = fields.ForeignKeyField("models.Usuario", related_name="deliveries", on_delete=fields.CASCADE)

    # 🔹 Relação com o cliente final
    customer = fields.ForeignKeyField("models.Customer", related_name="customer_deliveries", on_delete=fields.CASCADE)

    address = fields.TextField()  # Endereço
    latitude = fields.FloatField(null=True)
    longitude = fields.FloatField(null=True)
    total_distance_km = fields.FloatField(null=True)
    delivery_fee = fields.FloatField(null=True)
    total_price = fields.FloatField()  # Valor final da corrida.
    payment_status = fields.CharField(max_length=20, default="Pendente")  # pending, paid
    delivery_status = fields.CharField(max_length=20, default="esperando")  # waiting, on_route, delivered, canceled
    delivery_type = fields.CharField(max_length=10, default="moto")  # moto ou carro
    assigned_to = fields.CharField(max_length=90, null=True)  # entregador
    scheduled_time = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)  # data que a entrega foi criada


class DeliveryItem(models.Model):
    id = fields.IntField(pk=True)
    delivery = fields.ForeignKeyField("models.Delivery", related_name="items", on_delete=fields.CASCADE)
    product_id = fields.IntField()
    quantity = fields.IntField()
    price = fields.FloatField()
