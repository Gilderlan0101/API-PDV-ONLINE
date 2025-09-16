from datetime import datetime
from typing import Optional, Tuple, Any, List, Dict
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from dataclasses import dataclass, field

from src.model.user import Usuario
from src.model.employee import Employees
from src.model.product import Produto
from src.model.sale import Sales
from src.model.customers import Customer


@dataclass
class Checkout:
    """
    Classe para processar vendas: atualizar estoque, registrar venda e gerar nota fiscal.
    """

    user_id: int = field(default=0)
    product_name: str = field(default="")
    produto_id: int = field(default=0)
    quantity: int = field(default=0)
    payment_method: str = field(default="")
    total_price: float = field(default=0.0)
    lucro_total: float = field(default=0.0)
    funcionario_id: Optional[int] = field(default=None)
    funcionario_nome: Optional[str] = field(default=None)
    sale_code: Optional[str] = field(default=None)
    venda: Optional[Sales] = field(default=None)
    usuario: Optional[Usuario] = field(default=None)
    customer_id: Optional[int] = field(default=None)  # Adicionado customer_id
    installments: Optional[int] = field(default=None)  # Adicionado installments
    valor_recebido: Optional[float] = field(default=None)  # Adicionado valor_recebido
    troco: Optional[float] = field(default=None)  # Adicionado troco

    VALID_PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO', 'NOTA', 'FIADO', 'CARTÃO']

    def __post_init__(self):
        if self.payment_method and self.payment_method.upper() not in self.VALID_PAYMENT_METHODS:
            raise ValueError("Forma de pagamento inválida")
        self.status = False
        self._receipt_data = None

    def _set_receipt_data(self, itens: list[dict]):
        """Setter para os dados do recibo"""
        self._receipt_data = itens

    @property
    def receipt_data(self) -> Optional[list[dict]]:
        """Property para acessar os dados do recibo"""
        return self._receipt_data

    async def verify_datas(self) -> bool:
        """Verifica se os dados básicos estão presentes"""
        if not self.user_id:
            self.status = False
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
        if not self.product_name or not self.quantity:
            self.status = False
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe todos os dados")

        # Validações específicas por método de pagamento
        if self.payment_method.upper() == 'DINHEIRO':
            if self.valor_recebido is None or self.valor_recebido <= 0:
                raise HTTPException(status_code=400, detail="Valor recebido é obrigatório para pagamento em dinheiro")
            if self.troco is None:
                self.troco = 0.0

        if self.payment_method.upper() == 'CARTAO' and self.installments is None:
            self.installments = 1  # Default para 1 parcela

        self.status = True
        return self.status

    @staticmethod
    async def get_product_by_user(code: Optional[str] = None, name: Optional[str] = None) -> Optional[Produto]:
        """Busca produto por código ou nome"""
        query = Produto.all()
        if code:
            query = query.filter(id=int(code))
        if name:
            query = query.filter(name=name)
        return await query.first()

    def build_receipt(self, itens: list[dict]) -> dict:
        """Método regular para construir o recibo"""
        if not itens or not self.usuario:
            raise HTTPException(status_code=400, detail="Informações da venda incompletas")

        # Informações do cliente se existir
        cliente_info = {"Código Interno do Usuário": self.user_id}
        if self.customer_id:
            cliente_info["Cliente ID"] = self.customer_id

        receipt_data = {
            "Nota Fiscal": {
                "Empresa": {
                    "Razão Social": self.usuario.company_name,
                    "Nome Fantasia": self.usuario.trade_name or "Não informado",
                    "CNPJ": self.usuario.cnpj or "Não informado",
                    "Endereço": f'{getattr(self.usuario, "street", "")}, '
                    f'{getattr(self.usuario, "home_number", "")} - '
                    f'{getattr(self.usuario, "city", "")}/{getattr(self.usuario, "state", "")}',
                    "Inscrição Estadual": getattr(self.usuario, "state_registration", "Não informado"),
                    "Inscrição Municipal": getattr(self.usuario, "municipal_registration", "Não informado"),
                    "Operado por": self.funcionario_nome or self.usuario.username,
                    "codigo_da_venda": self.sale_code,
                },
                "Venda": [
                    {
                        "product_name": item["product_name"],
                        "Quantidade": item["quantity"],
                        "Preço Unitário": f'R$ {item["total_price"] / item["quantity"]:.2f}',
                        "Valor Total": f'R$ {item["total_price"]:.2f}',
                        "Lucro Total": f'R$ {item["lucro_total"]:.2f}',
                    }
                    for item in itens
                ],
                "Totais": {
                    "Valor Total Geral": f'R$ {sum(item["total_price"] for item in itens):.2f}',
                    "Lucro Total Geral": f'R$ {sum(item["lucro_total"] for item in itens):.2f}',
                },
                "Cliente": cliente_info,
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Forma de Pagamento": self.payment_method,
            }
        }

        # Adiciona informações específicas do método de pagamento
        if self.payment_method.upper() == 'DINHEIRO':
            receipt_data["Nota Fiscal"]["Pagamento"] = {"Valor Recebido": f'R$ {self.valor_recebido:.2f}', "Troco": f'R$ {self.troco:.2f}'}
        elif self.payment_method.upper() == 'CARTAO':
            receipt_data["Nota Fiscal"]["Pagamento"] = {"Parcelas": self.installments}
        elif self.payment_method.upper() == 'NOTA' and self.customer_id:
            receipt_data["Nota Fiscal"]["Pagamento"] = {"Tipo": "Venda em Nota", "Cliente ID": self.customer_id}

        receipt_data["Nota Fiscal"]["Observações"] = "Venda registrada com sucesso no sistema PDV."

        return receipt_data

    async def process_sale(
        self,
        current_user: Usuario,
        product_code: str,
        quantity: int,
        payment_method: str,
        funcionario_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        installments: Optional[int] = None,
        valor_recebido: Optional[float] = None,
        troco: Optional[float] = None,
    ) -> Tuple[dict, bool]:
        """Processa uma venda completa"""
        try:
            # Define admin_user e operador
            admin_user = current_user
            operador_id = funcionario_id
            operador_nome = getattr(current_user, "username", str(current_user))

            # Se current_user for funcionário, pega o admin dono
            funcionario_logado = await Employees.filter(id=current_user.id).first()
            if funcionario_logado and funcionario_logado.usuario_id:  # type: ignore
                admin_user = await Usuario.get(id=funcionario_logado.usuario_id)  # type: ignore
                operador_id = funcionario_logado.id
                operador_nome = funcionario_logado.nome

            # Se foi passado funcionario_id (venda feita por admin para funcionário)
            if funcionario_id:
                func_extra = await Employees.filter(
                    id=funcionario_id,
                    usuario_id=admin_user.id,
                ).first()
                if func_extra:
                    operador_id = func_extra.id
                    operador_nome = func_extra.nome

            self.funcionario_id = operador_id
            self.funcionario_nome = operador_nome
            self.user_id = admin_user.id
            self.payment_method = payment_method.upper()
            self.customer_id = customer_id
            self.installments = installments
            self.valor_recebido = valor_recebido
            self.troco = troco

            async with in_transaction() as connection:
                # Busca produto
                product = await self.get_product_by_user(code=product_code)
                if not product:
                    self.status = False
                    raise HTTPException(status_code=404, detail="Produto não encontrado")

                if product.stock < quantity:
                    self.status = False
                    raise HTTPException(status_code=400, detail="Estoque insuficiente")

                # Atualiza estoque
                product.stock -= quantity
                product.atualizado_em = datetime.now()
                await product.save(using_db=connection)

                # Calcula totais
                total_price = quantity * float(product.sale_price)
                lucro_total = (float(product.sale_price) - float(product.cost_price)) * quantity

                # Cria venda
                sale_data = {
                    "product_name": product.name,
                    "quantity": quantity,
                    "payment_method": payment_method,
                    "total_price": total_price,
                    "lucro_total": lucro_total,
                    "cost_price": float(product.cost_price),
                    "sale_code": self.sale_code,
                    "usuario_id": admin_user.id,
                    "produto_id": product.id,
                    "using_db": connection,
                }

                if self.funcionario_id:
                    sale_data["funcionario_id"] = self.funcionario_id

                if self.customer_id:
                    sale_data["customer_id"] = self.customer_id

                if self.installments:
                    sale_data["installments"] = self.installments

                if self.valor_recebido:
                    sale_data["valor_recebido"] = self.valor_recebido

                if self.troco:
                    sale_data["troco"] = self.troco

                self.venda = await Sales.create(**sale_data)
                self.usuario = admin_user

                # Prepara item para o recibo
                item_venda = {
                    "product_name": product.name,
                    "quantity": quantity,
                    "total_price": total_price,
                    "lucro_total": lucro_total,
                }

                self.status = True
                self._set_receipt_data([item_venda])

                # Retorna o recibo e status
                return self.build_receipt([item_venda]), self.status

        except Exception as e:
            self.status = False
            raise HTTPException(status_code=400, detail=f"Erro ao processar venda: {str(e)}")

    @staticmethod
    async def validating_information(
        current_user: Usuario,
        payment_method: str,
        employee_operator_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        installments: Optional[int] = None,
        valor_recebido: Optional[float] = None,
        troco: Optional[float] = None,
    ) -> dict:
        """Valida informações antes do processamento"""
        from src.utils.sales_code_generator import gerar_codigo_venda
        from src.controllers.car.cart_control import CartManagerDB

        cart = CartManagerDB()

        try:
            # Verifica se é um funcionário
            employee = await Employees.filter(id=current_user.id).first()

            if not employee:
                return {"success": False, "message": "Apenas funcionários podem realizar vendas"}

            employee_operator_id = employee.id
            employee_operator_name = employee.nome

            # Busca o usuário admin
            admin_user = await Usuario.get(id=employee.usuario_id)  # type: ignore

            if not admin_user:
                return {"success": False, "message": "Usuário admin não encontrado"}

            # Lista produtos do carrinho
            products = await cart.listar_produtos(admin_user.id)

            if not products:
                return {"success": False, "error": "Carrinho vazio"}

            # Validações específicas por método de pagamento
            if payment_method.upper() == 'DINHEIRO':
                if valor_recebido is None or valor_recebido <= 0:
                    return {"success": False, "error": "Valor recebido é obrigatório para pagamento em dinheiro"}
                if troco is None:
                    troco = 0.0

            if payment_method.upper() == 'CARTAO' and installments is None:
                installments = 1

            if payment_method.upper() == 'NOTA' and customer_id is None:
                return {"success": False, "error": "Customer ID é obrigatório para venda em nota"}

            # Processa cada produto
            sale_total = 0.0
            sale_details = []
            for prod in products:
                sale_total += prod.total_price
                sale_details.append(
                    {
                        "product_id": prod.product_id,
                        "product_name": prod.product_name,
                        "quantity": prod.quantity,
                        "unit_price": prod.price,
                    }
                )

            # Gera código de venda
            sale_code = gerar_codigo_venda()
            invoice = []
            last_checkout_instance = None

            for prod in sale_details:
                checkout = Checkout(
                    user_id=admin_user.id,
                    product_name=prod["product_name"],
                    produto_id=prod["product_id"],
                    quantity=prod["quantity"],
                    total_price=prod["quantity"] * prod["unit_price"],
                    lucro_total=0.0,
                    payment_method=payment_method.upper(),
                    funcionario_id=employee_operator_id,
                    funcionario_nome=employee_operator_name,
                    sale_code=sale_code,
                    customer_id=customer_id,
                    installments=installments,
                    valor_recebido=valor_recebido,
                    troco=troco,
                )

                # Processa a venda
                coupon, status = await checkout.process_sale(
                    current_user=admin_user,
                    product_code=str(prod["product_id"]),
                    quantity=prod["quantity"],
                    payment_method=payment_method.upper(),
                    funcionario_id=employee_operator_id,
                    customer_id=customer_id,
                    installments=installments,
                    valor_recebido=valor_recebido,
                    troco=troco,
                )

                if status:
                    invoice.append(coupon)
                    last_checkout_instance = checkout
                else:
                    return {"success": False, "error": "Erro ao processar a venda"}

            # Limpa carrinho e gera relatório
            await cart.limpar_carrinho(admin_user.id)
            from src.controllers.stoke.stoke_control import gerar_relatorio_completo

            report = await gerar_relatorio_completo(admin_user.id)

            return {
                "success": True,
                "data": {
                    "notas_fiscais": invoice,
                    "relatorio": report,
                    "total_venda": sale_total,
                    "codigo_da_venda": sale_code,
                    "funcionario_operador_id": employee_operator_id,
                    "funcionario_operador_nome": employee_operator_name,
                    "admin_id": admin_user.id,
                    "checkout_instance": last_checkout_instance,
                    "customer_id": customer_id,
                },
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


@dataclass
class Note(Checkout):
    """Extensão de Checkout para gerar notas fiscais adicionais"""

    async def verifyFields(self) -> bool:
        """Verifica campos obrigatórios"""
        campos_obrigatorios = [
            self.user_id,
            self.product_name,
            self.quantity,
            self.produto_id,
        ]
        if not all(campos_obrigatorios):
            raise HTTPException(status_code=400, detail="Preencha todos os campos obrigatórios.")
        if self.quantity <= 0:
            raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero.")
        return True

    async def createNote(self) -> dict:
        """Cria uma nota fiscal"""
        await self.verify_datas()
        await self.verifyFields()

        # Lógica específica para criação de nota
        if self.receipt_data:
            return self.build_receipt(self.receipt_data)
        else:
            raise HTTPException(status_code=400, detail="Nenhum dado de venda disponível")
