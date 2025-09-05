from fastapi import APIRouter, Depends
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=["Carrinho"])
cart = CartManagerDB()


@router.get("/")
async def listar_carrinho(current_user: Usuario = Depends(get_current_user)):
    """
    Lista todos os produtos no carrinho do usuário.
    """
    return await cart.listar_produtos(current_user.id)  # type: ignore
