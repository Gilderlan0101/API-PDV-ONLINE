from typing import Union
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from src.schemas.schema_user import SystemUser
from src.model.product import Produto
from src.model.user import Usuario
from src.model.employee import Employees
from src.auth.deps import get_current_user
from src.core.cache import client
from tortoise.exceptions import DoesNotExist

import json


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
                "error": "Usuário sem empresa vinculada.",
            }

        usuario_id = current_user.empresa_id
        cache_key = f"products:{usuario_id}"  # chave única por empresa

        # 🔹 Verifica cache
        cache = client.get(cache_key)
        if cache:
            print("Cache hit")
            return {"success": True, "data": json.loads(cache), "error": None}

        # 🔹 Se não tiver no cache, busca no banco
        products = await Produto.filter(usuario_id=usuario_id).all()
        products_data = jsonable_encoder(products)

        # Salva no Redis (com expiração de 60s, por exemplo)
        client.setex(cache_key, 60, json.dumps(products_data))

        return {"success": True, "data": products_data, "error": None}

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"success": False, "data": None, "error": f"Erro inesperado: {str(e)}"}
