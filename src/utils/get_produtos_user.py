from typing import Optional
from src.model.product import Produto


async def get_product_by_user(user_id: int, code: Optional[str] = None, name: Optional[str] = None) -> Optional[Produto]:
    """Busca produto pelo usuário, código ou nome."""
    query = Produto.filter(usuario_id=user_id)
    if code:
        query = query.filter(product_code=code)
    if name:
        query = query.filter(name=name)
    return await query.first()
