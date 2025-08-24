from datetime import datetime
import random
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
    """
    Classe responsável pelo processo de checkout de vendas.
    Registra a venda, atualiza o estoque e gera nota fiscal.
    """

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
        sale_code: Optional[str] = None,
    ) -> None:
        """
        Inicializa a instância de checkout.

        Args:
            user_id (int): ID do usuário que realiza a compra.
            product_name (str): Nome do produto.
            produto_id (int): ID do produto.
            quantity (int): Quantidade do produto.
            total_price (float, optional): Valor total da venda. Defaults to 0.0.
            lucro_total (float, optional): Lucro total da venda. Defaults to 0.0.
            payment_method (Optional[str], optional): Forma de pagamento. Defaults to None.
            funcionario_id (Optional[int], optional): ID do funcionário que realiza a venda. Defaults to None.
            funcionario_nome (Optional[str], optional): Nome do funcionário. Defaults to None.
            sale_code (Optional[str], optional): Código da venda. Defaults to None.
        """
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
        self.sale_code = sale_code

        if self.payment_method and self.payment_method not in [
            'pix',
            'cartão',
            'dinheiro',
            'nota',
        ]:
            raise ValueError("Forma de pagamento inválida")

    def verify_datas(self):
        """
        Verifica se os dados essenciais estão presentes.

        Returns:
            bool: True se os dados estiverem válidos, senão redireciona ou levanta HTTPException.
        """
        if not self.user_id:
            return RedirectResponse(url='/internal_login', status_code=302)
        if not self.product_name or not self.quantity:
            raise HTTPException(status_code=400, detail='Informe todos os dados')
        return True

    @staticmethod
    def get_product_by_user(
        session: Session, code: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[Produto]:
        """
        Busca um produto no banco pelo código ou nome.

        Args:
            session (Session): Sessão do SQLAlchemy.
            code (Optional[str], optional): Código do produto. Defaults to None.
            name (Optional[str], optional): Nome do produto. Defaults to None.

        Returns:
            Optional[Produto]: Produto encontrado ou None.
        """
        query = select(Produto)
        if code:
            query = query.where(
                Produto.id == int(code)
            )  # assume que product_code é o ID
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
        """
        Processa a venda: atualiza estoque, registra a venda e retorna a nota fiscal.

        Args:
            current_user: Usuário que realiza a venda.
            product_code (str): Código do produto.
            quantity (int): Quantidade vendida.
            payment_method (str): Forma de pagamento.
            funcionario_id (Optional[int], optional): ID do funcionário. Defaults to None.

        Returns:
            dict: Nota fiscal da venda.
        """
        self.user_id = current_user.id
        self.payment_method = payment_method

        with Session(engine) as session:
            product = self.get_product_by_user(session, code=product_code)
            if not product:
                raise HTTPException(status_code=404, detail='Produto não encontrado')

            if product.stock < quantity:
                raise HTTPException(status_code=400, detail='Estoque insuficiente')

            # Define nome do funcionário
            funcionario_nome = None
            if funcionario_id:
                from src.model.employee import Employees

                funcionario = session.get(Employees, funcionario_id)
                if funcionario:
                    funcionario_nome = funcionario.nome
                else:
                    # Se não encontrar no banco, usar o próprio usuário como operador
                    funcionario_nome = current_user.username
                    funcionario_id = current_user.id
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
                funcionario_id=funcionario_id,
                codigo_da_venda=self.sale_code,
            )
            session.add(self.venda)
            session.commit()
            session.refresh(self.venda)

            self.usuario = session.get(Usuario, current_user.id)
            self.funcionario_id = funcionario_id
            self.funcionario_nome = funcionario_nome

            return self.build_receipt()

    def build_receipt(self) -> dict:
        """
        Gera a nota fiscal da venda.

        Returns:
            dict: Estrutura completa da nota fiscal.
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
                    "Operado por": self.funcionario_nome or self.usuario.username,
                    'codigo_da_venda': self.sale_code,
                },
                'Venda': {
                    'Produto': self.product_name,
                    'Quantidade': self.quantity,
                    'Preço Unitário': f'R$ {self.total_price / self.quantity:.2f}',
                    'Valor Total': f'R$ {self.total_price:.2f}',
                    'Lucro Total': f'R$ {self.lucro_total:.2f}',
                    'Data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Forma de Pagamento': self.payment_method or 'Não especificada',
                    "Operado por": self.funcionario_nome or self.usuario.username,
                    'codigo_da_venda': self.sale_code,
                },
                'Cliente': {'Código Interno do Usuário': self.user_id},
                'Observações': 'Venda registrada com sucesso no sistema PDV.',
            }
        }


class Note(Checkout):
    """
    Extensão de Checkout para gerar notas fiscais adicionais.
    """

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
        sale_code: Optional[str] = None,
    ) -> None:
        """
        Inicializa a instância de nota.

        Args:
            user_id (int): ID do usuário.
            product_name (str): Nome do produto.
            produto_id (int): ID do produto.
            quantity (int): Quantidade.
            total_price (float): Valor total.
            lucro_total (float): Lucro total.
            payment_method (Optional[str], optional): Forma de pagamento. Defaults to None.
            funcionario_nome (Optional[str], optional): Nome do funcionário. Defaults to None.
            funcionario_id (Optional[int], optional): ID do funcionário. Defaults to None.
            sale_code (Optional[str], optional): Código da venda. Defaults to None.
        """
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
            sale_code=sale_code,
        )

    def verifyFields(self):
        """
        Verifica se os campos obrigatórios estão preenchidos.

        Raises:
            HTTPException: Se algum campo estiver vazio ou quantidade <= 0.

        Returns:
            bool: True se todos os campos estiverem corretos.
        """
        campos_obrigatorios = [
            self.user_id,
            self.product_name,
            self.quantity,
            self.produto_id,
        ]
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
        """
        Cria a nota fiscal verificando os dados.

        Returns:
            dict: Nota fiscal pronta.
        """
        if self.verify_datas() and self.verifyFields():
            return self.build_receipt()
