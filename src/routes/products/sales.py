from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.controllers.caixa.cash_controller import CashController, FinalizationObjcts
from src.auth.deps import get_current_user, SystemUser
from src.model.user import Usuario
from src.model.employee import Employees
from src.controllers.sales.sales import Checkout
from src.controllers.sales.validators import validating_information
from src.controllers.car.cart_control import CartManagerDB
from src.controllers.sales.delete_sales import delete_or_update_sale
from src.schemas.payments.payment_methods import InputData
from src.controllers.payments.partial import PartialPayment
from src.controllers.sales.services import processar_venda_carrinho

router = APIRouter()
cart = CartManagerDB()


@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix, nota, parcial"),
    customer_id: Optional[int] = Query(None, description="ID do cliente para venda em nota"),
    installments: Optional[int] = Query(None, description="Número de parcelas para cartão"),
    cpf: Optional[str] = Query(None, description='CPF passado dinamicamente em vendas parcias'),
    valor_recebido: Optional[float] = Query(None, description="Valor recebido em dinheiro"),
    troco: Optional[float] = Query(None, description="Troco para pagamento em dinheiro"),
    current_user: SystemUser = Depends(get_current_user),
):
    """
    Finaliza venda - para admin e funcionários.
    """
    try:
        # 🔹 Verifica se o usuário atual é um funcionário
        funcionario = await Employees.filter(id=current_user.id).first()

        if funcionario:
            employee_operator_id = current_user.id
            cart_owner_id = funcionario.id
        else:
            employee_operator_id = current_user.id
            cart_owner_id = current_user.id


        # 🔹 Verifica itens no carrinho
        cart_items = await cart.listar_produtos(cart_owner_id)
        print(cart_items)
        print(cart_items)
        print(cart_items)

        if not cart_items:
            raise HTTPException(status_code=400, detail="Carrinho vazio. Adicione produtos antes de finalizar a venda.")

        # 🔹 CORREÇÃO: Processar TODOS os itens do carrinho
        validation_process = await processar_venda_carrinho(
            user_id=current_user.empresa_id,
            cart_items=cart_items,
            payment_method=payment_method.upper(),
            employee_operator_id=employee_operator_id,
            customer_id=customer_id,
            installments=installments,
            cpf=cpf,
            valor_recebido=valor_recebido,
            troco=troco,
        )

        if not validation_process.get("success"):
            error_msg = validation_process.get("message") or validation_process.get("error") or "Erro ao processar venda"
            raise HTTPException(status_code=400, detail=error_msg)

        validation_data = validation_process.get("data", {})
        checkout_instance = validation_data.get("checkout_instance")

        if not checkout_instance or not hasattr(checkout_instance, 'venda'):
            raise HTTPException(status_code=500, detail="Instância do checkout inválida ou venda não processada")

        if not checkout_instance.venda or not hasattr(checkout_instance.venda, 'id'):
            raise HTTPException(status_code=500, detail="Venda não foi criada corretamente no processo de checkout")

        # 🔹 Atualiza valores do caixa
        caixa_aberto = await CashController.get_caixa_aberto_funcionario(employee_operator_id)
        if not caixa_aberto:
            raise HTTPException(status_code=404, detail=f"Atenção: Nenhum caixa aberto encontrado para o funcionário {employee_operator_id}")

        try:
            finalizacao = FinalizationObjcts(checkout_instance)
            await finalizacao.Updating_cash_values(caixa_aberto.id)

            sale_code = getattr(checkout_instance, 'sale_code', 'N/A')
            payment_method_final = getattr(checkout_instance, 'payment_method', payment_method.upper())
            total_venda = validation_data.get("total_venda", 0)

            resumo_venda = {
                "sale_code": sale_code,
                "total_venda": total_venda,
                "payment_method": payment_method_final,
                "funcionario_operador_id": employee_operator_id,
                "caixa_id": caixa_aberto.id,
                "customer_id": customer_id,
                "venda_id": checkout_instance.venda.id,
                "quantidade_itens": len(cart_items),  # 🔹 Adiciona quantidade de itens
            }

            await cart.limpar_carrinho(user_id=current_user.id)

        except Exception as e:
            print(f"Erro ao atualizar caixa (venda processada mas caixa não atualizado): {e}")

            sale_code = getattr(checkout_instance, 'sale_code', 'N/A')
            payment_method_final = getattr(checkout_instance, 'payment_method', payment_method.upper())
            total_venda = validation_data.get("total_venda", 0)

            resumo_venda = {
                "sale_code": sale_code,
                "total_venda": total_venda,
                "payment_method": payment_method_final,
                "funcionario_operador_id": employee_operator_id,
                "caixa_atualizado": False,
                "caixa_erro": str(e),
                "customer_id": customer_id,
                "venda_id": checkout_instance.venda.id if checkout_instance.venda else None,
                "quantidade_itens": len(cart_items),
            }

        return {"success": True, "message": "Venda finalizada com sucesso", "data": resumo_venda}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro interno ao processar venda: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
        import traceback

        print(f"Traceback completo: {traceback.format_exc()}")

        raise HTTPException(status_code=500, detail=f"Erro interno ao processar venda: {str(e)}")


@router.delete('/deleta/venda/')
async def delete_sale(
    product_id: int = Query(...),
    quantity: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user),
):
    """O usuario/funcionario pode deletar uma venda ou editar uma venda realizada."""

    # Verifica se o usuário atual é um funcionário
    funcionario = await Employees.filter(id=current_user.id).first()

    if funcionario:
        # Se for funcionário, usa o usuario_id do funcionário (ID do admin)
        user_id_carrinho = funcionario.usuario_id
    else:
        # Se não for funcionário, é admin e usa seu próprio ID
        user_id_carrinho = current_user.id

    result = await delete_or_update_sale(user_id_carrinho, product_id, quantity)
    return result


@router.post('/pagamento-parcial')
async def payment_partial(data: InputData, current_user: SystemUser = Depends(get_current_user)):

    try:

        if not current_user.id:
            raise HTTPException(status_code=400, detail='Usuario não encontrado.')

        data.user_id = current_user.id

        partial = PartialPayment(
            product=data.product_name, total_price=data.total_price, valor_recebido=data.valor_recebido, cpf=data.cpf, user_id=data.user_id
        )

        result = await partial.process_partial_sale()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Erro interno: {e}')

    except TypeError as e:
        raise HTTPException(status_code=500, detail=f'Erro interno: {e}')
