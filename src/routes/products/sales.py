from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import validating_information
from src.controllers.car.cart_control import CartManagerDB
from src.controllers.sales.delete_sales import delete_or_update_sale


router = APIRouter()
cart = CartManagerDB()

@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix, nota"),
    funcionario_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
):
    validation_process = await validating_information(
        current_user=current_user,
        payment_method=payment_method,
        employee_operator_id=funcionario_id
    )

    if validation_process is True:
        return validation_process
    else:
        return validation_process



@router.delete('/deleta/venda/')
async def delete_sale(
    product_id: int = Query(...),
    quantity: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
    # current_user: Usuario = Depends(get_current_user)
):
    """O usuario/fucionario pode deleta uma venda ou edita uma venda realiza.
    caso o fucionario delete a compra a quantidade de imtes volta para o stoke automaticamente
    """

    result = await delete_or_update_sale(current_user.id, product_id, quantity)
    match result:
        case True:
            return result
        case False:
            return result
