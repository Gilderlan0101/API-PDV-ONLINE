from src.schemas.payments.payment_methods import RegisterUserForPartialMode, VendaParcialData, AtualizaDividaData
from src.auth.deps import get_current_user, SystemUser
from src.routes.customer.customer_registration import customers
from fastapi import Depends, HTTPException, status
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

# Importe seus modelos
from src.model.partial import Partial, finished_debts

# Configurar logging
logger = logging.getLogger(__name__)

@customers.post('/cadastra-cliente-partial')
async def create_customers(data: RegisterUserForPartialMode, current_user: SystemUser = Depends(get_current_user)):
    """
    Endpoint para cadastrar um cliente para pagamentos parciais.
    """
    try:
        # Validação do CPF
        cpf_limpo = data.cpf.replace('.', '').replace('-', '')
        if len(cpf_limpo) != 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="CPF deve conter 11 dígitos"
            )

        # Validação do telefone
        tel_limpo = data.tel.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')

        # Verifica se o cliente já existe
        existing_customer = await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).first()
        
        if existing_customer:
            # Atualiza cliente existente
            await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).update(
                customers_name=data.full_name,
                tel=tel_limpo,
                produto=data.produto
            )
            mensagem = "Cliente atualizado com sucesso!"
        else:
            # Cria novo cliente
            await Partial.create(
                usuario_id=current_user.id,
                customers_name=data.full_name,
                cpf=cpf_limpo,
                tel=tel_limpo,
                produto=data.produto,
                value=0.0,  # Valor inicial zero
                payment_method=None
            )
            mensagem = "Cliente cadastrado com sucesso!"

        return {
            'status': 200,
            'mensagem': mensagem,
            'name': data.full_name,
            'tel': data.tel,
            'cpf': cpf_limpo,
            'produto': data.produto
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cadastrar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno: {str(e)}"
        )

@customers.post('/registra-venda')
async def registra_venda_parcial(data: VendaParcialData, current_user: SystemUser = Depends(get_current_user)):
    """
    Endpoint para registrar uma venda parcial.
    """
    try:
        # Validação do CPF
        cpf_limpo = data.cpf.replace('.', '').replace('-', '')
        if len(cpf_limpo) != 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="CPF inválido"
            )

        

        if data.valor_recebido > data.valor_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Valor recebido não pode ser maior que o valor total"
            )

        # Calcular saldo devedor
        saldo_devedor = data.valor_total - data.valor_recebido

        # Buscar cliente
        cliente = await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado. Cadastre o cliente primeiro."
            )

        # Atualizar dados do cliente com a venda
        await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).update(
            value=saldo_devedor,  # Saldo devedor
            payment_method=data.metodo_pagamento,
            produto=data.produto,
            date=datetime.now(ZoneInfo("America/Sao_Paulo"))
        )

        # Se a dívida foi totalmente paga, mover para finished_debts
        if saldo_devedor <= 0:
            # Buscar dados atualizados do cliente
            cliente_atualizado = await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).first()
            
            # Mover para finished_debts
            await finished_debts.create(
                usuario_id=current_user.id,
                name=cliente_atualizado.customers_name,
                tel=cliente_atualizado.tel,
                product_name=data.produto,
                value=data.valor_total,  # Valor total da venda
                payments={
                    "payment_method": data.metodo_pagamento,
                    "paid_value": data.valor_recebido,
                    "date": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
                }
            )
            
            # Remover da tabela Partial (dívida quitada)
            await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).delete()

        return {
            'status': 200,
            'mensagem': 'Venda parcial registrada com sucesso!',
            'cpf': cpf_limpo,
            'valor_recebido': data.valor_recebido,
            'saldo_devedor': saldo_devedor,
            'produto': data.produto,
            'status_divida': 'quitada' if saldo_devedor <= 0 else 'pendente'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar venda parcial: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno: {str(e)}"
        )

@customers.get('/dividas-atual')
async def get_dividas_atuais(current_user: SystemUser = Depends(get_current_user)):
    """
    Endpoint para buscar dívidas atuais do usuário.
    """
    try:
        # Buscar todas as dívidas pendentes na tabela Partial
        dividas = await Partial.filter(usuario_id=current_user.id).all()
        
        resultado = []
        for divida in dividas:
            resultado.append({
                'id': divida.id,
                'customers_name': divida.customers_name,
                'cpf': divida.cpf,
                'tel': divida.tel,
                'product_name': divida.produto,
                'value': divida.value if divida.value else 0.0,
                'payment_method': divida.payment_method,
                'date': divida.date.isoformat() if divida.date else None
            })

        return {
            'status': 200,
            'dividas': resultado,
            'total': len(resultado)
        }

    except Exception as e:
        logger.error(f"Erro ao buscar dívidas atuais: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno: {str(e)}"
        )

@customers.get('/dividas-pagas')
async def get_dividas_pagas(current_user: SystemUser = Depends(get_current_user)):
    """
    Endpoint para buscar histórico de dívidas pagas.
    """
    try:
        # Buscar todas as dívidas quitadas na tabela finished_debts
        dividas_pagas = await finished_debts.filter(usuario_id=current_user.id).all()
        
        resultado = []
        for divida in dividas_pagas:
            resultado.append({
                'id': divida.id,
                'name': divida.name,
                'tel': divida.tel,
                'product_name': divida.product_name,
                'paid_value': divida.value,  # Valor total pago
                'payments': divida.payments if divida.payments else {},
                'date': divida.date.isoformat() if divida.date else None,
                'status': 'Pago'
            })

        return {
            'status': 200,
            'dividas_pagas': resultado,
            'total': len(resultado)
        }

    except Exception as e:
        logger.error(f"Erro ao buscar dívidas pagas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno: {str(e)}"
        )

@customers.put('/atualiza-valor')
async def atualiza_valor_divida(data: AtualizaDividaData, current_user: SystemUser = Depends(get_current_user)):
    """
    Endpoint para atualizar valor da dívida (registrar pagamento).
    """
    try:
        # Validação do CPF
        cpf_limpo = data.cpf.replace('.', '').replace('-', '')
        if len(cpf_limpo) != 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="CPF inválido"
            )

        # Validação do valor
        if data.value_received <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Valor recebido deve ser maior que zero"
            )

        # Buscar a dívida atual
        divida = await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).first()
        
        if not divida:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma dívida encontrada para este CPF"
            )

        # Calcular novo saldo
        valor_atual = divida.value if divida.value else 0.0
        novo_saldo = valor_atual - data.value_received

        if novo_saldo < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valor pago é maior que o saldo devedor"
            )

        if novo_saldo == 0:
            # Dívida quitada - mover para finished_debts
            valor_total_pago = (valor_atual or 0) + data.value_received
            
            await finished_debts.create(
                usuario_id=current_user.id,
                name=divida.customers_name,
                tel=divida.tel,
                product_name=divida.produto,
                value=valor_total_pago,
                payments={
                    "payment_method": data.type_meyhod_payment,
                    "paid_value": data.value_received,
                    "date": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                    "last_payment": True
                }
            )
            
            # Remover da tabela Partial
            await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).delete()
            
            mensagem = "Dívida quitada com sucesso!"
            status_divida = "quitada"
        else:
            # Atualizar saldo devedor
            await Partial.filter(cpf=cpf_limpo, usuario_id=current_user.id).update(
                value=novo_saldo,
                payment_method=data.type_meyhod_payment,
                date=datetime.now(ZoneInfo("America/Sao_Paulo"))
            )
            
            mensagem = "Pagamento parcial registrado com sucesso!"
            status_divida = "pendente"

        return {
            'status': 200,
            'mensagem': mensagem,
            'cpf': cpf_limpo,
            'valor_pago': data.value_received,
            'novo_valor': novo_saldo if status_divida == "pendente" else 0,
            'ultimo_pagamento': data.value_received,
            'status_divida': status_divida
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar dívida: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno: {str(e)}"
        )