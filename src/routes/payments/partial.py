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
    Rota para registrar uma venda no modo PARCIAL (dívida em aberto) vinculada a um cliente.

    Args:
        data (InputData): Dados de entrada contendo:
            - product_name (str): Nome do produto.
            - total_price (float): Valor total da venda.
            - cpf (str): CPF do cliente.
            - user_id (int): ID do usuário responsável.
        current_user (SystemUser): Usuário autenticado, obtido via dependência.

    Returns:
        dict: Mensagem de sucesso ou erro no registro da dívida.

    Fluxo:
        1. Verifica se o produto existe para o usuário logado.
        2. Verifica se o cliente existe pelo CPF.
        3. Se não houver dívida ativa (value == 0), registra a nova dívida.
        4. Caso contrário, retorna mensagem informando dívida ativa.
    """

    try:
        # 🔹 1. Checar se o produto existe no estoque do usuário logado
        get_product = await get_product_by_user(user_id=current_user.empresa_id, code=None, name=data.product_name)

        if not get_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Produto '{data.product_name}' não está cadastrado.")

        # 🔹 2. Buscar cliente pelo CPF
        checking_client = await Partial.filter(usuario_id=current_user.empresa_id, cpf=data.cpf).first()

        if not checking_client:
            return {"message": "Cliente não encontrado."}

        # 🔹 3. Se cliente existe mas não tem dívida (value == 0 ou None), registrar nova dívida
        if not checking_client.value or checking_client.value == 0:
            await Partial.filter(
                usuario_id=current_user.empresa_id, # Sempre user empresa_id 
                cpf=data.cpf).update(value=data.total_price, product_name=data.product_name)

            # Buscar cliente atualizado
            updated_client = await Partial.filter(usuario_id=current_user.empresa_id, cpf=data.cpf).first()

            return {
                "message": "Dívida registrada com sucesso.",
                "response": {
                    "name": updated_client.customers_name,
                    "product": updated_client.product_name,
                    "value": updated_client.value,
                },
            }

        # 🔹 4. Cliente já tem dívida ativa
        return {"message": "O cliente já possui dívida ativa."}

    except HTTPException:
        raise  # re-levanta exceções HTTP sem alterar
    except Exception as e:
        # Captura erros inesperados
        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno ao tentar registrar venda em parcial: {e}"
        )


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno: {e}")
