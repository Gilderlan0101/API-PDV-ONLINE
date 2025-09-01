import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import Checkout
from src.controllers.stoke.stoke_control import gerar_relatorio_completo
from src.controllers.car.cart_control import CartManagerDB
from src.model.employee import Employees

router = APIRouter()
cart = CartManagerDB()


def gerar_codigo_venda(size: int = 6) -> str:
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(size)
    )


@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix"),
    funcionario_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
):
    """Finaliza a venda do usuário e retorna JSON padronizado para frontend"""
    try:
        produtos = await cart.listar_produtos(current_user.id)
        if not produtos:
            return {
                "success": False,
                "data": None,
                "error": "Carrinho vazio"
            }

        total_venda = 0.0
        venda_detalhes = []

        for prod in produtos:
            total_venda += prod.price_total
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
            # Definir funcionário responsável
            funcionario_operador_id = current_user.id
            funcionario_operador_nome = current_user.username

            if funcionario_id:
                funcionario = await Employees.get_or_none(id=funcionario_id)
                if funcionario:
                    funcionario_operador_id = funcionario.id
                    funcionario_operador_nome = funcionario.nome

            checkout = Checkout(
                user_id=current_user.id,
                product_name=prod["nome"],
                produto_id=prod["produto_id"],
                quantity=prod["quantidade"],
                total_price=prod["quantidade"] * prod["preco_unitario"],
                lucro_total=0.0,
                payment_method=payment_method.lower(),
                funcionario_id=funcionario_operador_id,
                funcionario_nome=funcionario_operador_nome,
                sale_code=sale_code,
            )

            nota = await checkout.process_sale(
                current_user=current_user,
                product_code=str(prod["produto_id"]),
                quantity=prod["quantidade"],
                payment_method=payment_method,
                funcionario_id=funcionario_operador_id,
            )
            notas_fiscais.append(nota)

        await cart.limpar_carrinho(current_user.id)
        relatorio = await gerar_relatorio_completo(current_user.id)

        return {
            "success": True,
            "data": {
                "notas_fiscais": notas_fiscais,
                "relatorio": relatorio,
                "total_venda": total_venda,
                "codigo_da_venda": sale_code
            },
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
