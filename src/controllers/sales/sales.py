import random
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from dataclasses import dataclass

from src.model.user import Usuario
from src.model.product import Produto
from src.model.sale import Sales


@dataclass
class Checkout:
    """
    Classe assíncrona usando Tortoise ORM para processar vendas:
    atualizar estoque, registrar venda e gerar nota fiscal.
    """

    user_id: int
    product_name: str
    produto_id: int
    quantity: int
    total_price: float = 0.0
    lucro_total: float = 0.0
    payment_method: Optional[str] = None
    funcionario_id: Optional[int] = None
    funcionario_nome: Optional[str] = None
    sale_code: Optional[str] = None
    venda: Optional[Sales] = None
    usuario: Optional[Usuario] = None

    VALID_PAYMENT_METHODS = ['pix', 'cartão', 'dinheiro', 'nota']

    def __post_init__(self):
        if self.payment_method and self.payment_method.lower() not in self.VALID_PAYMENT_METHODS:
            raise ValueError("Forma de pagamento inválida")

    async def verify_datas(self):
        if not self.user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
        if not self.product_name or not self.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe todos os dados")
        return True

    @staticmethod
    async def get_product_by_user(code: Optional[str] = None, name: Optional[str] = None) -> Optional[Produto]:
        query = Produto.all()
        if code:
            query = query.filter(id=int(code))
        if name:
            query = query.filter(name=name)
        return await query.first()

    async def process_sale(self, current_user: Usuario, product_code: str, quantity: int,
                           payment_method: str, funcionario_id: Optional[int] = None):
        self.user_id = current_user.id
        self.payment_method = payment_method.lower()

        async with in_transaction() as connection:
            product = await self.get_product_by_user(code=product_code)
            if not product:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            if product.stock < quantity:
                raise HTTPException(status_code=400, detail="Estoque insuficiente")

            # Define operador
            funcionario_nome = current_user.username
            if funcionario_id:
                from src.model.employee import Employees
                funcionario = await Employees.filter(id=funcionario_id).first()
                if funcionario:
                    funcionario_nome = funcionario.nome
                else:
                    funcionario_id = current_user.id

            self.product_name = product.name
            self.produto_id = product.id
            self.quantity = quantity
            self.total_price = quantity * float(product.sale_price)
            self.lucro_total = (float(product.sale_price) - float(product.cost_price)) * quantity
            self.funcionario_id = funcionario_id or current_user.id
            self.funcionario_nome = funcionario_nome

            await self.verify_datas()

            # Atualiza estoque
            product.stock -= quantity
            product.atualizado_em = datetime.now()
            await product.save(using_db=connection)

            # Registra venda
            self.venda = await Sales.create(
                produto_id=self.produto_id,
                product_name=self.product_name,
                quantity=self.quantity,
                total_price=self.total_price,
                lucro_total=self.lucro_total,
                cost_price=float(product.cost_price),
                usuario_id=current_user.id,
                funcionario_id=self.funcionario_id,
                codigo_da_venda=self.sale_code,
                using_db=connection
            )

            self.usuario = await Usuario.get(id=current_user.id)
            return self.build_receipt()

    def build_receipt(self) -> dict:
        if not self.venda or not self.usuario:
            raise HTTPException(status_code=400, detail="Informações da venda incompletas")

        return {
            'Nota Fiscal': {
                'Empresa': {
                    'Razão Social': self.usuario.company_name,
                    'Nome Fantasia': self.usuario.trade_name,
                    'CNPJ': self.usuario.cnpj,
                    'Endereço': f'{self.usuario.street}, {self.usuario.home_number} - {self.usuario.city}/{self.usuario.state}',
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
                    'Forma de Pagamento': self.payment_method,
                    "Operado por": self.funcionario_nome or self.usuario.username,
                    'codigo_da_venda': self.sale_code,
                },
                'Cliente': {'Código Interno do Usuário': self.user_id},
                'Observações': 'Venda registrada com sucesso no sistema PDV.',
            }
        }


class Note(Checkout):
    """Extensão de Checkout para gerar notas fiscais adicionais"""

    async def verifyFields(self):
        campos_obrigatorios = [self.user_id, self.product_name, self.quantity, self.produto_id]
        if not all(campos_obrigatorios):
            raise HTTPException(status_code=400, detail="Preencha todos os campos obrigatórios.")
        if self.quantity <= 0:
            raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero.")
        return True

    async def createNote(self):
        await self.verify_datas()
        await self.verifyFields()
        return self.build_receipt()
