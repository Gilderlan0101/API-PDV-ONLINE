from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from src.model.product import Produto
from src.model.user import Usuario
from src.auth.deps import get_current_user

list_products = APIRouter()


@list_products.get('/list', status_code=200)
async def list_all_products(current_user: Usuario = Depends(get_current_user)):
    """Lista todos os produtos do usuário com retorno padronizado para frontend"""
    try:
        products = await Produto.filter(usuario_id=current_user.id).all()

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


@list_products.get('/aviso-stoke', status_code=200)
async def aviso_stoke(current_user: Usuario = Depends(get_current_user)):
    """Lista produtos com estoque baixo ou vencidos, padronizado para frontend"""
    try:
        products_info = []
        products = await Produto.filter(usuario_id=current_user.id).all()

        # 🔹 Produtos com estoque baixo
        low_stock = [
            p.name for p in products 
            if p.stock is not None and p.stoke_min is not None and p.stock <= p.stoke_min
        ]
        if low_stock:
            products_info.append({"stoke": low_stock})

        # 🔹 Produtos vencidos hoje
        today = datetime.today().date()
        expired_today = [
            p.name for p in products 
            if p.date_expired is not None and p.date_expired.date() <= today
        ]
        if expired_today:
            products_info.append({"vencidos": expired_today})

        return {
            "success": True,
            "data": jsonable_encoder(products_info),
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
