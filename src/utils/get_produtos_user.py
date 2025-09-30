import json
from typing import Optional
from src.model.product import Produto
from src.core.cache import client

async def get_product_by_user(user_id: int, code: Optional[str] = None, name: Optional[str] = None):
    """Busca produto pelo usuário, código ou nome."""

    cache_key = f"product:{user_id}:{code or ''}:{name or ''}"
    cache = client.get(cache_key)

    if cache:
        return json.loads(cache)  # volta dict

    query = Produto.filter(usuario_id=user_id)
    if code:
        query = query.filter(product_code=code)
    if name:
        query = query.filter(name=name)

    product = await query.first().values()  # <-- pega dict direto

    if product:
        client.setex(cache_key, 90, json.dumps(product, default=str))  # salva no Redis
    return product
