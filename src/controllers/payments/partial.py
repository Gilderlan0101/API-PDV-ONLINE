from src.model.partial import Partial, finished_debts
from tortoise.exceptions import DoesNotExist
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException, status
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

# Configuração de logging
LOGGER = logging.getLogger(__name__)

class Person:
    """
    Classe responsável por criar cliente antes de venda no modo parcial
    """
    
    def __init__(self, full_name: str, cpf: str, tel: str, user_id: int):
        self.full_name = full_name
        self.cpf = self._clean_cpf(cpf)
        self.tel = self._clean_phone(tel)
        self.user_id = user_id

    def _clean_cpf(self, cpf: str) -> str:
        """Remove caracteres especiais do CPF"""
        return cpf.replace('.', '').replace('-', '')

    def _clean_phone(self, tel: str) -> str:
        """Remove caracteres especiais do telefone"""
        return tel.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')

    async def create_customer(self) -> bool:
        """
        Cria cliente se não existir
        Retorna True se criou, False se já existe
        """
        try:
            existing_customer = await Partial.filter(cpf=self.cpf, usuario_id=self.user_id).first()
            
            if not existing_customer:
                await Partial.create(
                    usuario_id=self.user_id,
                    customers_name=self.full_name,
                    cpf=self.cpf,
                    tel=self.tel,
                    produto="",  # Produto será definido na venda
                    value=0.0,
                    payment_method=None
                )
                LOGGER.info(f"Cliente {self.full_name} criado com sucesso")
                return True
                
            LOGGER.info(f"Cliente {self.full_name} já existe")
            return False
            
        except Exception as error:
            LOGGER.error(f"Erro ao criar cliente: {str(error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao criar cliente"
            )


class PartialPayment:
    """
    Classe para processar pagamentos parciais de dívidas
    """
    
    def __init__(self, payment_method: str, value_received: float, cpf: str, user_id: int):
        self.payment_method = payment_method.upper()
        self.value_received = value_received
        self.cpf = self._clean_cpf(cpf)
        self.user_id = user_id

    def _clean_cpf(self, cpf: str) -> str:
        """Remove caracteres especiais do CPF"""
        return cpf.replace('.', '').replace('-', '')

    async def update_value(self) -> dict:
        """
        Processa pagamento parcial de uma dívida
        
        Fluxo:
        1. Valida dados de entrada
        2. Busca dívida do cliente
        3. Calcula novo saldo
        4. Registra pagamento no histórico
        5. Atualiza ou remove dívida
        6. Retorna resultado
        """
        
        # Validação inicial dos dados
        self._validate_input_data()
        
        # Busca dívida do cliente
        debt_record = await self._get_customer_debt()
        
        # Calcula novo saldo após pagamento
        current_balance, remaining_balance = await self._calculate_new_balance(debt_record)
        
        # Registra pagamento no histórico
        await self._register_payment_history(debt_record, current_balance, remaining_balance)
        
        # Atualiza ou remove dívida conforme saldo
        result = await self._update_or_remove_debt(debt_record, remaining_balance, current_balance)
        
        return result

    def _validate_input_data(self) -> None:
        """Valida dados de entrada do pagamento"""
        if not self.cpf or len(self.cpf) != 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF deve conter 11 dígitos"
            )

        if self.value_received is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valor recebido é obrigatório"
            )

        try:
            paid_value = Decimal(str(self.value_received))
            if paid_value <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Valor recebido deve ser maior que zero"
                )
        except (InvalidOperation, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valor recebido inválido"
            )

    async def _get_customer_debt(self) -> Partial:
        """Busca dívida do cliente na base de dados"""
        debt_record = await Partial.filter(cpf=self.cpf, usuario_id=self.user_id).first()
        
        if not debt_record:
            LOGGER.warning(f"Dívida não encontrada para CPF: {self.cpf}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma dívida encontrada para este CPF"
            )
            
        return debt_record

    async def _calculate_new_balance(self, debt_record: Partial) -> tuple:
        """Calcula novo saldo após pagamento"""
        try:
            current_balance = Decimal(str(debt_record.value or "0"))
            paid_value = Decimal(str(self.value_received))
            
            LOGGER.info(f"Saldo atual: {current_balance}, Pagamento: {paid_value}")
            
            if paid_value > current_balance:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pagamento maior que dívida: R$ {paid_value} > R$ {current_balance}"
                )
                
            remaining_balance = float(current_balance) - float(paid_value)
            return current_balance, remaining_balance
            
        except (InvalidOperation, ValueError) as error:
            LOGGER.error(f"Erro no cálculo do saldo: {str(error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro no cálculo do saldo"
            )

    async def _register_payment_history(self, debt_record: Partial, 
                                  current_balance: Decimal, 
                                  remaining_balance: float) -> None:
        """Registra pagamento no histórico de dívidas quitadas"""
        try:
            payment_data = {
                "date": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                "payment_method": self.payment_method,
                "paid_value": float(self.value_received),
                "previous_balance": float(current_balance),
                "new_balance": remaining_balance
            }

            # 🔥 MUDANÇA CRÍTICA: Verifica se já existe registro para este CPF
            existing_finished_debt = await finished_debts.filter(
                cpf=debt_record.cpf,
                usuario_id=self.user_id,
                product_name=debt_record.produto
            ).first()

            if existing_finished_debt:
                # 🔥 ATUALIZA registro existente
                payment_history = existing_finished_debt.payment_history or []
                payment_history.append(payment_data)
                
                # Atualiza totais
                existing_finished_debt.total_paid_value += float(self.value_received)
                existing_finished_debt.payment_history = payment_history
                
                # Se a dívida foi quitada, atualiza status
                if remaining_balance <= 0:
                    existing_finished_debt.status = "quitada"
                
                await existing_finished_debt.save()
                LOGGER.info(f"Pagamento adicionado ao histórico existente para {debt_record.customers_name}")
                
            else:
                # 🔥 CRIA novo registro apenas se não existir
                await finished_debts.create(
                    name=debt_record.customers_name,
                    product_name=debt_record.produto,
                    cpf=debt_record.cpf,
                    tel=debt_record.tel,
                    original_debt_value=float(current_balance) + float(self.value_received),  # Valor original total
                    total_paid_value=float(self.value_received),
                    payment_history=[payment_data],  # Array com primeiro pagamento
                    status="parcial" if remaining_balance > 0 else "quitada",
                    usuario_id=self.user_id,
                )
                LOGGER.info(f"Novo histórico criado para {debt_record.customers_name}")
                
        except Exception as error:
            LOGGER.error(f"Erro ao registrar pagamento no histórico: {str(error)}")
            # Não interrompe fluxo principal se falhar registro histórico


            
    async def _update_or_remove_debt(self, debt_record: Partial, 
                                   remaining_balance: float, 
                                   current_balance: Decimal) -> dict:
        """Atualiza ou remove dívida conforme saldo restante"""
        try:
            if remaining_balance <= 0:
                # Dívida totalmente quitada
                change = abs(remaining_balance)
                await debt_record.delete()
                
                LOGGER.info(f"Dívida quitada para CPF: {self.cpf}")
                
                return {
                    "message": "Dívida quitada com sucesso",
                    "cpf": self.cpf,
                    "novo_valor": 0.0,
                    "change": change,
                    "status": "quitada"
                }
            else:
                # Atualiza saldo da dívida
                debt_record.value = float(remaining_balance)
                debt_record.payment_method = self.payment_method
                debt_record.date = datetime.now(ZoneInfo("America/Sao_Paulo"))
                await debt_record.save()
                
                LOGGER.info(f"Pagamento parcial registrado para CPF: {self.cpf}")
                
                return {
                    "message": "Pagamento parcial registrado",
                    "cpf": self.cpf,
                    "novo_valor": float(remaining_balance),
                    "ultimo_pagamento": float(self.value_received),
                    "status": "pendente"
                }
                
        except Exception as error:
            LOGGER.error(f"Erro ao atualizar dívida: {str(error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao atualizar dívida"
            )

    @staticmethod
    async def get_current_debts(user_id: int) -> dict:
        """Obtém todas as dívidas atuais do usuário"""
        try:
            debts = await Partial.filter(usuario_id=user_id).all()
            result = []
            
            for debt in debts:
                result.append({
                    'id': debt.id,
                    'customers_name': debt.customers_name,
                    'cpf': debt.cpf,
                    'tel': debt.tel,
                    'product_name': debt.produto,
                    'value': debt.value if debt.value else 0.0,
                    'payment_method': debt.payment_method,
                    'date': debt.date.isoformat() if debt.date else None,
                })

            LOGGER.info(f"Encontradas {len(result)} dívidas para usuário {user_id}")
            
            return {
                'status': 200, 
                'dividas': result, 
                'total': len(result)
            }
            
        except Exception as error:
            LOGGER.error(f"Erro ao buscar dívidas: {str(error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao buscar dívidas"
            )

    @staticmethod
    async def get_paid_debts(user_id: int) -> dict:
        """Obtém histórico de dívidas quitadas"""
        try:
            paid_debts = await finished_debts.filter(usuario_id=user_id).all()
            result = []
            
            for debt in paid_debts:
                # 🔥 MUDANÇA: Agora usa total_paid_value que é a soma real
                result.append({
                    'id': debt.id,
                    'name': debt.name,
                    'tel': debt.tel,
                    'cpf': debt.cpf,  # 🔥 ADICIONA CPF
                    'product_name': debt.product_name,
                    'paid_value': debt.total_paid_value or 0,  # 🔥 SOMA REAL dos pagamentos
                    'original_value': debt.original_debt_value or 0,
                    'payment_history': debt.payment_history or [],  # 🔥 Histórico completo
                    'total_payments': len(debt.payment_history or []),  # 🔥 Quantidade de pagamentos
                    'status': debt.status,
                    'date': debt.date.isoformat() if debt.date else None,
                })

            LOGGER.info(f"Encontradas {len(result)} dívidas pagas para usuário {user_id}")
            
            return {
                'status': 200, 
                'dividas_pagas': result, 
                'total': len(result)
            }
            
        except Exception as error:
            LOGGER.error(f"Erro ao buscar dívidas pagas: {str(error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao buscar dívidas pagas"
            )

    @staticmethod
    def _calculate_total_paid(debt) -> float:
        """Calcula valor total pago a partir dos pagamentos"""
        total_paid = 0.0
        
        if debt.payments and isinstance(debt.payments, dict):
            if 'paid_value' in debt.payments:
                total_paid += float(debt.payments.get('paid_value', 0))
            # Adicione mais lógica se houver estrutura complexa de pagamentos
            
        return total_paid if total_paid > 0 else (debt.value or 0)