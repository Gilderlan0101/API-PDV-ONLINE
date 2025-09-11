from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.controllers.caixa.cash_controller import CashController, FinalizationObjcts
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import Checkout
from src.controllers.car.cart_control import CartManagerDB
from src.controllers.sales.delete_sales import delete_or_update_sale


router = APIRouter()
cart = CartManagerDB()

@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix, nota"),
    
    current_user: Usuario = Depends(get_current_user),
):
    """
    Finaliza venda - APENAS para funcionários
    """

    try:

        

        validation_process = await Checkout.validating_information(
            current_user=current_user, 
            payment_method=payment_method,
            employee_operator_id= current_user.id  # employee_operator_id: È o propior usuario logado   
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
