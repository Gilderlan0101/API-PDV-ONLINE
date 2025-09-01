from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from tortoise.exceptions import DoesNotExist

from src.model.user import Usuario
from src.model.product import Produto
from src.auth.deps import get_current_user

buscar_produtos = APIRouter()


async def get_product_by_user(user_id: int, code: Optional[str] = None, name: Optional[str] = None) -> Optional[Produto]:
    """Busca produto pelo usuário, código ou nome."""
    query = Produto.filter(usuario_id=user_id)
    if code:
        query = query.filter(product_code=code)
    if name:
        query = query.filter(name=name)
    return await query.first()


@buscar_produtos.get('/buscar', status_code=200)
async def get_product(
    code: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user)
):
    """Busca produto por código ou nome e retorna JSON padronizado para frontend"""
    try:
        if not code and not name:
            return {
                "success": False,
                "data": None,
                "error": "Informe código ou nome do produto"
            }

        product = await get_product_by_user(current_user.id, code, name)

        if not product:
            return {
                "success": False,
                "data": None,
                "error": "Produto não encontrado"
            }

        return {
            "success": True,
            "data": jsonable_encoder(product),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
