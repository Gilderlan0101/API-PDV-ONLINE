from typing import Optional
from src.model.product import Produto
from src.model.customers import Customer
from src.model.user import Usuario
import re


def to_dict(model) -> dict:
    """
    Converte um objeto Tortoise ORM em dicionário.
    """
    return {field: getattr(model, field) for field in model._meta.fields_map}


async def get_product_by_user(
    user_id: int,
    code: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Produto]:
    """
    Busca um produto vinculado a um usuário com filtros opcionais.
    """
    query = Produto.filter(usuario_id=user_id)
    if code:
        query = query.filter(product_code=code)
    if name:
        query = query.filter(name=name)
    return await query.first()


async def get_customers(user_id: int, customer_name: Optional[str] = None, cpf: Optional[str] = None) -> Optional[Customer]:
    """
    🔍 Busca clientes do usuário atual com filtros opcionais.
    """
    query = Customer.filter(usuario_id=user_id)

    if customer_name:
        query = query.filter(full_name__icontains=customer_name)
    if cpf:
        cpf_clean = re.sub(r'\D', '', cpf)
        query = query.filter(cpf__contains=cpf_clean)

    return await query.first()
