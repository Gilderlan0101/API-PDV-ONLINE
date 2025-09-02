from fastapi import APIRouter, Depends, Query
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=["Carrinho"])
cart = CartManagerDB()


@router.post("/adicionar")
async def adicionar_produto(
    product_id: int = Query(..., description="ID do produto a ser adicionado"),
    quantity: int = Query(..., gt=0, description="Quantidade do produto"),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Adiciona um produto ao carrinho do usuário.
    """
    return await cart.add_produto(product_id, quantity, current_user.id)  
