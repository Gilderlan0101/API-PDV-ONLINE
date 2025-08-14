import random
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import Checkout
from src.controllers.stoke.stoke_control import gerar_relatorio_completo

router = APIRouter()

@router.post('/vendas', status_code=status.HTTP_200_OK)
async def register_sale(
    code: str = Query(..., description='Código do produto'),
    quantity: int = Query(..., gt=0, description='Quantidade vendida'),
    payment_method: str = Query(..., description='Forma de pagamento: dinheiro, cartão, pix'),
    funcionario_id: Optional[int] = Query(None, description='ID do funcionário que realizou a venda'),
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user or not current_user.id:
        raise HTTPException(status_code=401, detail='Usuário não autenticado')
    
    # Gerando um codigo de vendas aleatorio
    sale_code = lambda size=6: ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(size))

    checkout = Checkout(
        user_id=current_user.id,
        product_name='',
        produto_id=0,
        quantity=quantity,
        total_price=0.0,
        lucro_total=0.0,
        payment_method=payment_method,
        funcionario_id=funcionario_id,
        sale_code=sale_code()
    )

    nota_fiscal = checkout.process_sale(
        current_user=current_user,
        product_code=code,
        quantity=quantity,
        payment_method=payment_method,
        funcionario_id=funcionario_id,
    )
    
    # Gerar relatório de estoque e validade
    relatorio = gerar_relatorio_completo(current_user.id)

    return {
        "nota_fiscal": nota_fiscal,
        "relatorio": relatorio
    }
