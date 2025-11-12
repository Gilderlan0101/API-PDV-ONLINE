from fastapi import APIRouter, Depends, Body, HTTPException
from src.controllers.car.cart_control import CartManagerDB
from src.auth.deps_employes import SystemEmployees, get_current_employee

router = APIRouter(tags=["Carrinho"])


@router.post("/adicionar")
async def adicionar_produto(
    product_id: int = Body(..., description="ID do produto"),
    quantity: int = Body(..., gt=0, description="Quantidade"),
    current_user: SystemEmployees = Depends(get_current_employee),
):
    """
    Adiciona um produto ao carrinho. Dados recebidos via BODY.
    """
    empresa_id = current_user.empresa_id
    employee_id = current_user.id

    cart = CartManagerDB(company_id=empresa_id, employee_id=employee_id)

    if not empresa_id or not employee_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida")

    # A função add_produto é responsável por lidar com o carrinho
    return await cart.add_produto(product_id=product_id, quantity=quantity, empresa_id=empresa_id, employee_id=employee_id)
