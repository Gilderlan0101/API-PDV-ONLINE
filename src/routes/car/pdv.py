# from fastapi import APIRouter, Depends, Query
# from src.auth.deps import get_current_user
# from src.model.user import Usuario
# from src.controllers.car.cart_control import CartManagerDB

# router = APIRouter()
# cart = CartManagerDB()

# @router.post("/carrinho/adicionar")
# async def adicionar_produto(
#     product_id: int = Query(...),
#     quantity: int = Query(..., gt=0),
#     current_user: Usuario = Depends(get_current_user)
# ):
#     return await cart.add_produto(product_id, quantity, current_user.id) # type: ignore

# @router.delete("/carrinho/remover/{product_id}")
# async def remover_produto(
#     product_id: int,
#     current_user: Usuario = Depends(get_current_user)
# ):
#     return await cart.remove_produto(product_id, current_user.id) # type: ignore

# @router.delete("/carrinho/limpar")
# async def limpar_carrinho(current_user: Usuario = Depends(get_current_user)):
#     return await cart.limpar_carrinho(current_user.id) # type: ignore

# @router.get("/carrinho")
# async def listar_carrinho(current_user: Usuario = Depends(get_current_user)):
#     return await cart.listar_produtos(current_user.id) # type: ignore


# @router.delete("/carrinho/remover_por_venda")
# async def remover_produtos_por_venda(
#     sale_code: str = Query(..., description="Código da venda para remover produtos do carrinho"),
#     current_user: Usuario = Depends(get_current_user)
# ):
#     """
#     Remove produtos do carrinho baseado no código da venda.
#     Útil para devoluções ou trocas.
#     """
#     return await cart.remover_produtos_por_venda(sale_code)
