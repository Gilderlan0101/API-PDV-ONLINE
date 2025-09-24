from fastapi import APIRouter, HTTPException, status, Depends
from src.controllers.payments.partial import PartialPayment
from src.schemas.payments.payment_methods import InputData, ReceivePaymentPartial
from src.model.partial import Partial
from src.auth.deps import get_current_user, SystemUser
from src.utils.get_produtos_user import get_product_by_user


partial = APIRouter()


__PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO']


@partial.post('/registra-venda')
async def registre_sale_in_partial(data: InputData, current_user: SystemUser = Depends(get_current_user)):
    """
    Rota responsável por registrar uma venda em "partial" (dívida em aberto) no nome de um cliente.

    Args:
        data (InputData): Dados de entrada contendo:
            - product_name (str): Nome do produto.
            - total_price (float | int): Valor da venda.
            - cpf (str): CPF do cliente.
            - user_id (int): ID do usuário responsável.
        current_user (SystemUser): Usuário autenticado, obtido via dependência.

    Returns:
        dict: Mensagem de sucesso ou erro no registro da dívida.
              Exemplo: {"message": "Dívida registrada com sucesso."}

    Notas:
        - Antes de registrar a venda, é verificado se o cliente existe pelo CPF.
        - Caso o cliente seja encontrado e não possua valor pendente (`value == 0`),
          o campo `value` será atualizado para o valor de `data.total_price`.
        - Se já houver dívida ativa, nenhuma alteração é feita.
    """

    try:
        # Checando se cliente existe antes de abrir uma dívida no nome dele
        checking_client = await Partial.filter(usuario_id=current_user.empresa_id, cpf=data.cpf).first()
        get_product = get_product_by_user(user_id=current_user.empresa_id, code=None, name=data.product_name)

        if get_product:

            if checking_client:
                # Verificando se o value é == 0
                if checking_client.value is None:
                    # Atualizando valor
                    await Partial.filter(usuario_id=current_user.empresa_id, cpf=data.cpf).update(value=data.total_price, product_name=data.product_name)

                    # Buscando cliente novamente para exibir os dados atualizado
                    updated_client = await Partial.filter(usuario_id=current_user.empresa_id, cpf=data.cpf).first()

                    for c in updated_client:

                        return {
                            "message": "Dívida registrada com sucesso.",
                            "response": [
                                {
                                    "name": c.customers_name,
                                    "product": c.product_name,
                                    "value": c.value,
                                }
                            ],
                        }

                else:
                    return {"message": "O cliente já possui dívida ativa."}

            else:
                return {"message": "Cliente não encontrado."}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'{dta.product_name} Não esta cadastrado.')

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao tentar registrar venda em partial: {e}")


@partial.get('/dividas-atual')
async def get_all_active_debts(current_user: SystemUser = Depends(get_current_user)):
    '''
    get_all_active_debts: Responsavel por buscar todas as dividas abertas

    params: current_user

    returns:
        {
            "customers_name": parcial.customers_name,
            "cpf": parcial.cpf,
            "tel": parcial.tel,
            "product_name": parcial.product_name,
            "value": parcial.value,
    }

    '''

    return await PartialPayment.view(user_id=current_user.id)



@partial.get('/dividas-pagas')
async def paids(current_user: SystemUser = Depends(get_current_user)):
    '''
    get_all_active_debts: Responsavel por buscar todas as dividas pagas
    '''
 
    return await PartialPayment.debts_paid(user_id=current_user.empresa_id)


@partial.put('/atualiza-valor')
async def update_pending_debt(data: ReceivePaymentPartial, current_user: SystemUser = Depends(get_current_user)):
    '''Comportamento:
    - valida valor recebido;
    - subtrai o valor recebido do valor atual;
    - se o novo valor <= 0, deleta o registro e retorna possível troco;
    - caso contrário, salva o novo valor e retorna o registro atualizado.
    '''

    try:

        if data.type_meyhod_payment.upper() in __PAYMENT_METHODS:

            # Buscando cleinte e atualizand valor no banco de dados
            update_value = PartialPayment(
                value_received=data.value_received, cpf=data.cpf, user_id=current_user.empresa_id, payment_method=data.type_meyhod_payment
            )

            update_value.checks_fields()

        else:
            raise HTTPException(
                # Method Not Allowed
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Selecione uma forma de pagamento valida.",
            )

        return await update_value.update_value()

    except Exception as e:
        print(e)
