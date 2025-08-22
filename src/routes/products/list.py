from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlmodel import Session, select
from src.model.user import Usuario
from src.model.product import Produto
from src.auth.deps import get_current_user
from src.conf.database import engine

list_products = APIRouter()

@list_products.get('/list', status_code=200)
async def list_all_products(current_user: Usuario = Depends(get_current_user)):
    """Lista todos os produtos do usuário com retorno padronizado para frontend"""
    try:
        with Session(engine) as session:
            statement = select(Produto).where(Produto.usuario_id == current_user.id)
            products = session.exec(statement).all()

            return {
                "success": True,
                "data": jsonable_encoder(products),
                "error": None
            }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
