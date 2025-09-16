from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.controllers.caixa.cash_controller import CashController, FinalizationObjcts
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.model.employee import Employees
from src.controllers.sales.sales import Checkout
from src.controllers.car.cart_control import CartManagerDB
from src.controllers.sales.delete_sales import delete_or_update_sale

router = APIRouter()
cart = CartManagerDB()

@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix, nota"),
    customer_id: Optional[int] = Query(None, description="ID do cliente para venda em nota"),
    installments: Optional[int] = Query(None, description="Número de parcelas para cartão"),
    valor_recebido: Optional[float] = Query(None, description="Valor recebido em dinheiro"),
    troco: Optional[float] = Query(None, description="Troco para pagamento em dinheiro"),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Finaliza venda - para admin e funcionários
    """

    try:
        # Verifica se o usuário atual é um funcionário
        funcionario = await Employees.filter(id=current_user.id).first()
        
        if funcionario:
            # Se for funcionário, o operador é o próprio funcionário
            employee_operator_id = current_user.id
            # O dono do carrinho é o admin (usuario_id do funcionário)
            cart_owner_id = funcionario.usuario_id
        else:
            # Se for admin, o operador é o próprio admin
            employee_operator_id = current_user.id
            cart_owner_id = current_user.id

        # Primeiro, obtém os itens do carrinho para verificar se há itens
        cart_items = await cart.listar_produtos(cart_owner_id)
        if not cart_items:
            raise HTTPException(status_code=400, detail="Carrinho vazio. Adicione produtos antes de finalizar a venda.")

        validation_process = await Checkout.validating_information(
            current_user=current_user, 
            payment_method=payment_method,
            employee_operator_id=employee_operator_id,
            customer_id=customer_id,
            installments=installments,
            valor_recebido=valor_recebido,
            troco=troco
        ) 
        
        if not validation_process.get("success"):
            error_msg = validation_process.get("message") or validation_process.get("error") or "Erro ao processar venda"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Obtém a instância do checkout
        checkout_instance = validation_process["data"].get("checkout_instance")
        
        if not checkout_instance:
            raise HTTPException(status_code=500, detail="Instância do checkout não retornada")
        
        # Processa atualização do caixa
        funcionario_operador_id = validation_process["data"]["funcionario_operador_id"]
        caixa_aberto = await CashController.get_caixa_aberto_funcionario(funcionario_operador_id)
        
        if not caixa_aberto:
            # Pode ser crítico ou apenas um aviso, dependendo da regra de negócio
            print(f"Atenção: Nenhum caixa aberto encontrado para o funcionário {funcionario_operador_id}")
            # Se for crítico, descomente a linha abaixo:
            # raise HTTPException(status_code=400, detail="Nenhum caixa aberto para o funcionário")
        else:
            try:
                finalizacao = FinalizationObjcts(checkout_instance)
                await finalizacao.Updating_cash_values(caixa_aberto.id)
                print("Caixa atualizado com sucesso!")
                
                # Adiciona informação do caixa na resposta
                validation_process["data"]["caixa_atualizado"] = True
                validation_process["data"]["caixa_id"] = caixa_aberto.id
                
            except Exception as e:
                print(f"Erro ao atualizar caixa (venda processada mas caixa não atualizado): {e}")
                validation_process["data"]["caixa_atualizado"] = False
                validation_process["data"]["caixa_erro"] = str(e)
        
        # Limpa o carrinho após finalizar a venda
        await cart.limpar_carrinho(cart_owner_id)
        
        return validation_process
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro inesperado ao finalizar venda: {e}")
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