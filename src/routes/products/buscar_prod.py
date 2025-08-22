from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session
from src.model.user import Usuario
from src.model.product import Produto
from src.auth.deps import get_current_user
from src.conf.database import engine
from src.routes.products.helpers import get_product_by_user

buscar_produtos = APIRouter()

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

        with Session(engine) as session:
            product = get_product_by_user(session, current_user.id, code, name)  # type: ignore

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
