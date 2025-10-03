from fastapi import APIRouter, Depends, Query
from src.auth.deps import get_current_user, SystemUser

# from src.model.user import Usuario
from src.model.employee import Employees

from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=["Carrinho"])


cart = CartManagerDB()


@router.post("/adicionar")
async def adicionar_produto(
    product_id: int = Query(..., description="ID do produto a ser adicionado"),
    quantity: int = Query(..., gt=0, description="Quantidade do produto"),
    current_user: SystemUser = Depends(get_current_user),
):
    """
    Adiciona um produto ao carrinho do usuário ou funcionário.
    """
    # sempre usar empresa_id para amarrar ao dono
    user_id_carrinho = current_user.empresa_id

    return await cart.add_produto(product_id, quantity, user_id_carrinho)
