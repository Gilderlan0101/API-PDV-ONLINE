from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from dataclasses import dataclass

from src.conf.database import engine
from src.model.sale import Sales
from src.model.user import Usuario
from src.model.product import Produto


@dataclass
class Checkout:
    def __init__(
        self,
        user_id: int,
        product_name: str,
        produto_id: int,
        quantity: int,
        total_price: float = 0.0,
        lucro_total: float = 0.0,
        payment_method: Optional[str] = None,
        funcionario_id: Optional[int] = None,
        funcionario_nome: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.product_name = product_name
        self.produto_id = produto_id
        self.quantity = quantity
        self.total_price = total_price
        self.lucro_total = lucro_total
        self.payment_method = payment_method
        self.funcionario_id = funcionario_id
        self.funcionario_nome = funcionario_nome
        self.venda = None
        self.usuario = None

        if self.payment_method and self.payment_method not in ['pix', 'cartão', 'dinheiro', 'nota']:
            raise ValueError("Forma de pagamento inválida")

    def verify_datas(self):
        if not self.user_id:
            # Redireciona caso não tenha usuário (exemplo de segurança)
            return RedirectResponse(url='/internal_login', status_code=302)
        if not self.product_name or not self.quantity:
            raise HTTPException(status_code=400, detail='Informe todos os dados')
        return True

    @staticmethod
    def get_product_by_user(session: Session, user_id: int, code: Optional[str] = None, name: Optional[str] = None) -> Optional[Produto]:
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
        funcionario_id: Optional[int] = None,
    ):
        self.user_id = current_user.id
        self.payment_method = payment_method

        with Session(engine) as session:
            product = self.get_product_by_user(session, user_id=current_user.id, code=product_code)
            if not product:
                raise HTTPException(status_code=404, detail='Produto não encontrado')

            if product.stock < quantity:
                raise HTTPException(status_code=400, detail='Estoque insuficiente')

            # Pega dados do funcionário ou do próprio usuário (dono)
            funcionario_nome = None
            if funcionario_id:
                from src.model.employee import Employees
                funcionario = session.get(Employees, funcionario_id)
                if not funcionario:
                    raise HTTPException(status_code=404, detail='Funcionário não encontrado')
                funcionario_nome = funcionario.nome
            else:
                funcionario_nome = current_user.username
                funcionario_id = current_user.id

            self.product_name = product.name
            self.produto_id = product.id
            self.quantity = quantity
            self.total_price = quantity * product.sale_price
            self.lucro_total = (product.sale_price - product.cost_price) * quantity

            if self.verify_datas() is not True:
                return self.verify_datas()

            # Atualiza estoque
            product.stock -= quantity
            product.atualizado_em = datetime.now()
            session.add(product)

            # Registra a venda
            self.venda = Sales(
                produto_id=self.produto_id,
                product_name=self.product_name,
                quantity=self.quantity,
                total_price=self.total_price,
                lucro_total=self.lucro_total,
                cost_price=product.cost_price,
                usuario_id=current_user.id,
                funcionario_id=funcionario_id
            )
            session.add(self.venda)
            session.commit()
            session.refresh(self.venda)

            self.usuario = session.get(Usuario, current_user.id)
            self.funcionario_id = funcionario_id
            self.funcionario_nome = funcionario_nome

            return self.build_receipt()

    def build_receipt(self) -> dict:
        if not self.venda or not self.usuario:
            raise HTTPException(status_code=400, detail='Informações da venda incompletas')

        return {
            'Nota Fiscal': {
                'Empresa': {
                    'Razão Social': self.usuario.company_name,
                    'Nome Fantasia': self.usuario.trade_name,
                    'CNPJ': self.usuario.cnpj,
                    'Endereço': f'{self.usuario.street}, {self.usuario.number} - {self.usuario.city}/{self.usuario.state}',
                    'Inscrição Estadual': self.usuario.state_registration,
                    'Inscrição Municipal': self.usuario.municipal_registration,
                    "Operado por": self.funcionario_nome or self.usuario.username
                },
                'Venda': {
                    'Produto': self.product_name,
                    'Quantidade': self.quantity,
                    'Preço Unitário': f'R$ {self.total_price / self.quantity:.2f}',
                    'Valor Total': f'R$ {self.total_price:.2f}',
                    'Lucro Total': f'R$ {self.lucro_total:.2f}',
                    'Data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Forma de Pagamento': self.payment_method or 'Não especificada',
                    "Operado por": self.funcionario_nome or self.usuario.username
                },
                'Cliente': {'Código Interno do Usuário': self.user_id},
                'Observações': 'Venda registrada com sucesso no sistema PDV.',
            }
        }


class Note(Checkout):
    def __init__(
        self,
        user_id: int,
        product_name: str,
        produto_id: int,
        quantity: int,
        total_price: float,
        lucro_total: float,
        payment_method: Optional[str] = None,
        funcionario_nome: Optional[str] = None,
        funcionario_id: Optional[int] = None,
    ) -> None:
        super().__init__(
            user_id=user_id,
            product_name=product_name,
            produto_id=produto_id,
            quantity=quantity,
            total_price=total_price,
            lucro_total=lucro_total,
            payment_method=payment_method,
            funcionario_nome=funcionario_nome,
            funcionario_id=funcionario_id,
        )

    def verify_datas(self):
        return super().verify_datas()

    def verifyFields(self):
        campos_obrigatorios = [self.user_id, self.product_name, self.quantity, self.produto_id]
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
