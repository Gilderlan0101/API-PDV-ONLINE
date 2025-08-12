import datetime
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from src.conf.database import engine
from src.model.user.users import Produto, Sales, Usuario
from dataclasses import dataclass

"""Desenvolvimento interno"""
# import os
# import sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# import datetime
# from datetime import datetime
# from typing import Optional

# from fastapi import HTTPException
# from fastapi.responses import RedirectResponse
# from sqlmodel import Session, select
# from conf.database import engine
# from model.user.users import Produto, Sales, Usuario
# from dataclasses import dataclass
"""Fim do bloco de codigo"""

@dataclass
class Checkout:
    def __init__(
        self,
        user_id: int,
        product_name: str,
        quantity: int,
        total_price: float,
        lucro_total: float,
        payment_method: Optional[str] = None,  # Forma de pagamento opcional
    ) -> None:
        self.user_id = user_id
        self.product_name = product_name
        self.quantity = quantity
        self.total_price = total_price
        self.lucro_total = lucro_total
        self.payment_method = payment_method
        self.total = 0
        self.venda = None  # Será preenchido após a venda
        self.usuario = None  # Também será usado no recibo
        
        if self.payment_method not in ['pix', 'cartão', 'dinheiro', 'nota']:
            raise ValueError("Forma de pagamento inválida")

    def build_receipt(self) -> dict:
        """
        Monta os dados da nota fiscal de venda em formato profissional.
        """
        if not self.venda or not self.usuario:
            raise HTTPException(
                status_code=400, detail='Informações da venda incompletas'
            )

        return {
            'Nota Fiscal': {
                'Empresa': {
                    'Razão Social': self.usuario.company_name,
                    'Nome Fantasia': self.usuario.trade_name,
                    'CNPJ': self.usuario.cnpj,
                    'Endereço': f'{self.usuario.street}, {self.usuario.number} - {self.usuario.city}/{self.usuario.state}',
                    'Inscrição Estadual': self.usuario.state_registration,
                    'Inscrição Municipal': self.usuario.municipal_registration,
                },
                'Venda': {
                    'Produto': self.product_name,
                    'Quantidade': self.quantity,
                    'Preço Unitário': f'R$ {self.total_price / self.quantity:.2f}',
                    'Valor Total': f'R$ {self.total_price:.2f}',
                    'Lucro Total': f'R$ {self.lucro_total:.2f}',
                    'Data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Forma de Pagamento': self.payment_method or 'Não especificada',
                },
                'Cliente': {'Código Interno do Usuário': self.user_id},
                'Observações': 'Venda registrada com sucesso no sistema PDV.',
            }
        }

    def verify_datas(self):
        """Verifica se os dados principais foram fornecidos corretamente."""
        if not self.user_id:
            # Redireciona para login se não houver usuário autenticado
            return RedirectResponse(url='/internal_login', status_code=302)

        if not self.product_name or not self.quantity:
            raise HTTPException(status_code=400, detail='Informe todos os dados')

        return True

    @staticmethod
    def get_product_by_user(
        session: Session,
        user_id: int,
        code: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Produto]:
        """Busca o produto pelo nome ou código, filtrando por usuário."""
        query = select(Produto).where(Produto.usuario_id == user_id)

        if code:
            query = query.where(Produto.product_code == code)
        if name:
            query = query.where(Produto.name == name)

        return session.exec(query).first()

    def process_sale(
        self,
        current_user,
        product_code: str,
        quantity: int,
        payment_method: str,
    ):
        """
        Recebe dados da venda, valida, registra e retorna a nota completa.
        """
        self.user_id = current_user.id
        self.payment_method = payment_method

        with Session(engine) as session:
            # Busca o produto pelo código e usuário
            product = self.get_product_by_user(
                session, user_id=current_user.id, code=product_code
            )

            if not product:
                raise HTTPException(status_code=404, detail='Produto não encontrado')

            if product.stock < quantity:
                raise HTTPException(status_code=400, detail='Estoque insuficiente')

            # Atualiza atributos da venda
            self.product_name = product.name
            self.quantity = quantity
            self.total_price = quantity * product.sale_price
            self.lucro_total = (product.sale_price - product.cost_price) * quantity
            self.total = self.total_price

            # Valida dados obrigatórios
            if self.verify_datas() is not True:
                return self.verify_datas()

            # Atualiza o estoque
            product.stock -= quantity
            product.atualizado_em = datetime.now()
            session.add(product)

            # Registra a venda no banco
            self.venda = Sales(
                product_name=self.product_name,
                quantity=self.quantity,
                total_price=self.total_price,
                lucro_total=self.lucro_total,
                cost_price=product.cost_price,
                usuario_id=current_user.id,
            )
            session.add(self.venda) # type: ignore
            session.commit()
            session.refresh(self.venda)

            # Pega dados do usuário para montar a nota
            self.usuario = session.get(Usuario, current_user.id)

            # Retorna nota fiscal completa
            return self.build_receipt()


class Note(Checkout):
    def __init__(
        self,
        user_id: int,
        product_name: str,
        quantity: int,
        total_price: float,
        lucro_total: float,
        payment_method: Optional[str] = None,
    ) -> None:
        super().__init__(
            user_id,
            product_name,
            quantity,
            total_price,
            lucro_total,
            payment_method,
        )

    def verify_datas(self):
        return super().verify_datas()

    def verifyFields(self):
        campos_obrigatorios = [self.user_id, self.product_name, self.quantity]
        if not all(campos_obrigatorios):
            raise HTTPException(
                status_code=400,
                detail='Preencha todos os campos obrigatórios.',
            )
        if self.quantity <= 0:
            raise HTTPException(
                status_code=400, detail='A quantidade deve ser maior que zero.'
            )
        return True

    def createNote(self):
        if self.verify_datas() and self.verifyFields():
            return self.build_receipt()
