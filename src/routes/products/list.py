from typing import Union
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from src.schemas.schema_user import SystemUser
from src.model.product import Produto
from src.model.user import Usuario
from src.model.employee import Employees
from src.auth.deps import  get_current_user
from tortoise.exceptions import DoesNotExist

list_products = APIRouter()
@list_products.get('/list', status_code=200)
async def list_all_products(current_user: SystemUser = Depends(get_current_user)):
    """
    Lista todos os produtos do usuário ou do funcionário vinculado à empresa.
    """
    try:
        if not current_user.empresa_id:
            return {
                "success": False,
                "data": None,
                "error": "Usuário sem empresa vinculada."
            }

        usuario_id = current_user.empresa_id
        print(f"[DEBUG] ID da empresa para busca: {usuario_id}")

        products = await Produto.filter(usuario_id=usuario_id).all()
        print(f"[DEBUG] Total de produtos encontrados: {len(products)}")

        return {
            "success": True,
            "data": jsonable_encoder(products),
            "error": None
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
