from fastapi import APIRouter, Depends, Query
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=["Carrinho"])
cart = CartManagerDB()


@router.delete("/remover/{product_id}")
async def remover_produto(
    product_id: int, current_user: Usuario = Depends(get_current_user)
):
    """
    Remove um produto específico do carrinho.
    """
    return await cart.remove_produto(product_id, current_user.id)  # type: ignore


@router.delete("/limpar")
async def limpar_carrinho(current_user: Usuario = Depends(get_current_user)):
    """
    Limpa todos os produtos do carrinho do usuário.
    """
    return await cart.limpar_carrinho(current_user.id)  # type: ignore


@router.delete("/remover_por_venda")
async def remover_produtos_por_venda(
    sale_code: str = Query(
        ..., description="Código da venda para remover produtos do carrinho"
    ),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Remove produtos do carrinho baseado no código da venda.
    Útil para devoluções ou trocas.
    """
    return await cart.remover_produtos_por_venda(sale_code)
