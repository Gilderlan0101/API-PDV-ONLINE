from src.controllers.sales.sales import Checkout
from src.model.partial import Partial, finished_debts
from tortoise.exceptions import DoesNotExist
from decimal import Decimal, InvalidOperation
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from datetime import datetime
from zoneinfo import ZoneInfo


class Person:
    '''Class responsavel por cria um cliente antes de criar uma venda no modo partial'''

    def __init__(self, full_name, cpf: str, tel: str, user_id):

        self.full_name = full_name
        self.cpf = cpf
        self.tel = tel
        self.user_id = user_id

    async def create_customer(self):
        customers = await Partial.filter(cpf=self.cpf).first()
        if not customers:

            create = await Partial.create(usuario_id=self.user_id, customers_name=self.full_name, cpf=self.cpf, tel=self.tel)

            return True
        return False


class PartialPayment:
    """
    Classe para processar pagamentos parciais.
    """

    def __init__(self, payment_method: str, value_received: int, cpf: str, user_id: int):
        """
        Inicializa a venda parcial, herdando Checkout.
        """

        self.payment_method = payment_method
        self.value_received = value_received
        self.cpf = cpf
        self.user_id = user_id

    def checks_fields(self) -> bool:

        if self.value_received and self.cpf and self.user_id != ' ':
            return True
        return False

    async def update_value(self) -> dict:
        """
        Processa um pagamento parcial de um cliente no PDV.

        Fluxo:
        1. Valida entrada (CPF, valor recebido > 0).
        2. Busca a dívida parcial (`Partial`) associada ao CPF.
        3. Subtrai o valor recebido do saldo devedor.
        4. Registra o pagamento em `finished_debts` (histórico).
        5. Atualiza ou remove o registro de dívida, conforme o caso.
        6. Retorna status com novo valor e/ou troco.

        Auto-recuperação:
        - Sempre tenta evitar crash (try/except).
        - Se algum campo inválido for passado, retorna HTTPException clara.
        """

        # =====================
        # 1. Validação inicial
        # =====================
        if not getattr(self, "cpf", None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF não informado.")

        if self.value_received is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valor_recebido é obrigatório.")

        try:
            paid_value = Decimal(str(self.value_received))
        except (InvalidOperation, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valor_recebido inválido.")

        if paid_value <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="valor_recebido deve ser maior que zero.")

        # =====================
        # 2. Busca dívida parcial
        # =====================
        async with in_transaction():
            table_partial = await Partial.filter(cpf=self.cpf).first()

            if not table_partial:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma dívida parcial encontrada para este CPF.")

        # =====================
        # 3. Calcula novo saldo
        # =====================
        try:
            current_value = Decimal(str(table_partial.value or "0"))
        except (InvalidOperation, ValueError):
            current_value = Decimal("0")

        remaining_value = current_value - paid_value

        # =====================
        # 4. Salva relatório de pagamento
        # =====================
        try:
            payment_data = {
                "date": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                "payment_method": self.payment_method,
                "paid_value": float(round(paid_value, 2)),  # <<< valor pago (não saldo)
            }

            await finished_debts.create(
                name=table_partial.customers_name,
                product_name=table_partial.product_name,
                cpf=table_partial.cpf,
                tel=table_partial.tel,
                value=float(round(paid_value, 2)),  # <<< valor recebido neste pagamento
                payments=payment_data,  # JSON com detalhes
                usuario_id=self.user_id,
            )
        except Exception as e:
            # Melhor log para debug interno
            print(f"⚠️ Erro ao salvar finished_debts: {e}")

        # =====================
        # 5. Atualiza ou deleta dívida
        # =====================
        try:
            if remaining_value <= 0:
                # Troco se o cliente pagou a mais
                change = float(round((paid_value - current_value) if paid_value > current_value else Decimal("0"), 2))

                # Remove dívida porque foi quitada
                await table_partial.delete()

                return {"message": "✅ Dívida quitada e registro removido.", "cpf": table_partial.cpf, "novo_valor": 0.0, "change": change}

            # Atualiza saldo parcial
            table_partial.value = float(round(remaining_value, 2))
            table_partial.payment_method = self.payment_method
            table_partial.date = datetime.now(ZoneInfo("America/Sao_Paulo"))
            await table_partial.save()

        except Exception as e:
            print(f"⚠️ Erro ao atualizar dívida parcial: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao atualizar dívida.")

        # =====================
        # 6. Resposta final
        # =====================
        return {"cpf": table_partial.cpf, "novo_valor": table_partial.value, "ultimo_pagamento": float(round(paid_value, 2))}

    @staticmethod
    async def view(user_id: int):
        """Visualiza todas as dívidas parciais do usuário"""
        table_partial = await Partial.filter(usuario_id=user_id).all()
        return [
            {
                "customers_name": parcial.customers_name,
                "cpf": parcial.cpf,
                "tel": parcial.tel,
                "product_name": parcial.product_name,
                "value": parcial.value,
            }
            for parcial in table_partial
        ]

    @staticmethod
    async def debts_paid(user_id: int):
        """Visualiza todas as dívidas parciais do usuário"""
        paid = await finished_debts.filter(usuario_id=user_id).all()
        return [
            {
                "name": parcial.name,
                "tel": parcial.tel,
                "product_name": parcial.product_name,
                "value": parcial.value,
                "payments": parcial.payments,
                "status": "OK",
            }
            for parcial in paid
        ]

    # async def create_account_partial(self, user_id: int, full_name: str, )
