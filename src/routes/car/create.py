from fastapi import APIRouter, Body, Depends, HTTPException

from src.auth.deps_employes import SystemEmployees, get_current_employee
from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=['Carrinho'])


@router.post('/adicionar')
async def adicionar_produto(
    product_id: int = Body(..., gt=0),  # 🎯 gt=0 garante > 0
    quantity: int = Body(..., gt=0),  # 🎯 gt=0 garante > 0
    current_user: SystemEmployees = Depends(get_current_employee),
):
    """
    Adiciona um produto ao carrinho. Dados recebidos via BODY.
    """
    empresa_id = current_user.empresa_id
    employee_id = current_user.id

    # 🎯 VALIDAÇÃO EXPLÍCITA
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Quantidade deve ser maior que zero',
        )

    if product_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='ID do produto inválido',
        )

    print(f'🔍 DEBUG ROTA:')
    print(f'  product_id: {product_id} (type: {type(product_id)})')
    print(f'  quantity: {quantity} (type: {type(quantity)})')

    cart = CartManagerDB(company_id=empresa_id, employee_id=employee_id)
    return await cart.add_produto(product_id=product_id, quantity=quantity)
