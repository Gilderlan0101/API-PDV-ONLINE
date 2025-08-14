import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status

from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import Checkout
from src.controllers.stoke.stoke_control import gerar_relatorio_completo
from src.controllers.car.cart_control import CartManagerDB

router = APIRouter()
cart = CartManagerDB()


def gerar_codigo_venda(size: int = 6) -> str:
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(size)
    )


@router.post("/vendas/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(
        ..., description="Forma de pagamento: dinheiro, cartão, pix"
    ),
    funcionario_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
):
    produtos = await cart.listar_produtos(current_user.id)
    if not produtos:
        raise HTTPException(status_code=400, detail="Carrinho vazio")

    total_venda = 0.0
    venda_detalhes = []

    for prod in produtos:
        total_venda += prod.total_price
        venda_detalhes.append(
            {
                "produto_id": prod.product_id,
                "nome": prod.product_name,
                "quantidade": prod.quantity,
                "preco_unitario": prod.price,
            }
        )

    sale_code = gerar_codigo_venda()
    notas_fiscais = []

    for prod in venda_detalhes:
        checkout = Checkout(
            user_id=current_user.id,
            product_name=prod["nome"],
            produto_id=prod["produto_id"],
            quantity=prod["quantidade"],
            total_price=prod["quantidade"] * prod["preco_unitario"],
            lucro_total=0.0,
            payment_method=payment_method,
            funcionario_id=funcionario_id,
            sale_code=sale_code,
        )
        nota = checkout.process_sale(
            current_user=current_user,
            product_code=str(prod["produto_id"]),
            quantity=prod["quantidade"],
            payment_method=payment_method,
            funcionario_id=funcionario_id,
        )
        notas_fiscais.append(nota)

    await cart.limpar_carrinho(current_user.id)
    relatorio = gerar_relatorio_completo(current_user.id)

    return {
        "notas_fiscais": notas_fiscais,
        "relatorio": relatorio,
        "total_venda": total_venda,
        "codigo_da_venda": sale_code,
    }
