from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
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
    if not code and not name:
        raise HTTPException(status_code=400, detail="Informe código ou nome do produto")

    with Session(engine) as session:
        product = get_product_by_user(session, current_user.id, code, name) # type: ignore
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return jsonable_encoder(product)  # <-- transforma SQLModel em JSON

