# routes/cart_update.py
from fastapi import APIRouter, Depends
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.car.cart_control import CartManagerDB
from src.schemas.carrinho import EditCartItem

router = APIRouter()
cart = CartManagerDB()

@router.post("/atualizar")
async def atualizar_item(
    item: EditCartItem,
    current_user: Usuario = Depends(get_current_user),
):
    return await cart.update_produto(
        product_id=item.product_id,
        user_id=current_user.id, # type: ignore
        quantity=item.quantity,
        discount=item.discount,
        addition=item.addition,replace_quantity=item.replace_quantity,
        replace_discount=item.replace_discount,
        replace_addition=item.replace_addition,
    )
