from datetime import datetime

from typing import Optional
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from dataclasses import dataclass

from src.model.user import Usuario
from src.model.employee import Employees
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
    payment_method: str
    total_price: float = 0.0
    lucro_total: float = 0.0
    funcionario_id: Optional[int] = None
    funcionario_nome: Optional[str] = None
    sale_code: Optional[str] = None
    venda: Optional[Sales] = None
    usuario: Optional[Usuario] = None

    VALID_PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO', 'NOTA', 'FIADO']

    def __post_init__(self):
        if self.payment_method and self.payment_method not in self.VALID_PAYMENT_METHODS:
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

    async def process_sale(
        self,
        current_user: Usuario,  # ✅ Agora recebe objeto Usuario, não ID
        product_code: str,
        quantity: int,
        payment_method: str,
        funcionario_id: Optional[int] = None,
    ):
        try:
            print(f"CHECKOUT_DEBUG: Iniciando process_sale")
            print(f"CHECKOUT_DEBUG: current_user.id={current_user.id}, user_id={self.user_id}")

            # 🔹 Define admin_user e operador
            admin_user = current_user  # ✅ Já é objeto Usuario
            operador_id = funcionario_id
            operador_nome = current_user.username if hasattr(current_user, "username") else str(current_user)

            # 🔹 Se current_user for funcionário, pega o admin dono
            funcionario_logado = await Employees.filter(id=current_user.id).first()
            if funcionario_logado and funcionario_logado.usuario_id:  # type: ignore
                # ✅ CORRETO: Busca o usuário admin pelo ID
                admin_user = await Usuario.get(id=funcionario_logado.usuario_id)  # type: ignore
                operador_id = funcionario_logado.id
                operador_nome = funcionario_logado.nome

            # 🔹 Se foi passado funcionario_id (venda feita por admin para funcionário)
            if funcionario_id:
                func_extra = await Employees.filter(
                    id=funcionario_id,
                    usuario_id=admin_user.id,  # ✅ Usa admin_user.id (inteiro)
                ).first()
                if func_extra:
                    operador_id = func_extra.id
                    operador_nome = func_extra.nome

            self.funcionario_id = operador_id
            self.funcionario_nome = operador_nome
            self.user_id = admin_user.id  # ✅ Armazena apenas o ID
            self.payment_method = payment_method
            self.sale_code = self.sale_code

            async with in_transaction() as connection:
                # 🔹 Busca produto
                product = await self.get_product_by_user(code=product_code)
                if not product:
                    raise HTTPException(status_code=404, detail="Produto não encontrado")

                if product.stock < quantity:
                    raise HTTPException(status_code=400, detail="Estoque insuficiente")

                # 🔹 Atualiza estoque
                product.stock -= quantity
                product.atualizado_em = datetime.now()
                await product.save(using_db=connection)

                # 🔹 Cria venda
                sale_data = {
                    "product_name": product.name,
                    "quantity": quantity,
                    "payment_method": payment_method,
                    "total_price": quantity * float(product.sale_price),
                    "lucro_total": (float(product.sale_price) - float(product.cost_price)) * quantity,
                    "cost_price": float(product.cost_price),
                    "sale_code": self.sale_code,
                    "usuario_id": admin_user.id,  # Usa o ID
                    "produto_id": product.id,
                    "using_db": connection,
                }
                if self.funcionario_id:
                    sale_data["funcionario_id"] = self.funcionario_id

                self.venda = await Sales.create(**sale_data)
                self.usuario = admin_user  # Mantém objeto para build_receipt

                item_venda = {
                    "product_name": product.name,
                    "quantity": quantity,
                    "total_price": quantity * float(product.sale_price),
                    "lucro_total": (float(product.sale_price) - float(product.cost_price)) * quantity,
                }

                return self.build_receipt([item_venda])  # ✅ Passa uma lista com um item

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"CHECKOUT_DEBUG: ERRO em process_sale: {str(e.__class__.__name__)}")

    def build_receipt(self, itens: list[dict]) -> dict:
        if not self.venda or not self.usuario:
            raise HTTPException(status_code=400, detail="Informações da venda incompletas")

        return {
            "Nota Fiscal": {
                "Empresa": {
                    "Razão Social": self.usuario.company_name,
                    "Nome Fantasia": self.usuario.trade_name,
                    "CNPJ": self.usuario.cnpj,
                    "Endereço": f'{getattr(self.usuario, "street", "")}, '
                    f'{getattr(self.usuario, "number", "")} - '
                    f'{getattr(self.usuario, "city", "")}/{getattr(self.usuario, "state", "")}',
                    "Inscrição Estadual": getattr(self.usuario, "state_registration", ""),
                    "Inscrição Municipal": getattr(self.usuario, "municipal_registration", ""),
                    "Operado por": self.funcionario_nome or self.usuario.username,
                    "codigo_da_venda": self.sale_code,
                },
                # Aqui "Venda" passa a ser uma lista de produtos
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
                "Cliente": {"Código Interno do Usuário": self.user_id},
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Forma de Pagamento": self.payment_method,
                "Observações": "Venda registrada com sucesso no sistema PDV.",
            }
        }


@dataclass
class Note(Checkout):
    """Extensão de Checkout para gerar notas fiscais adicionais"""

    async def verifyFields(self):
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

    async def createNote(self):
        await self.verify_datas()
        await self.verifyFields()


# Procesa carrinho antes de finaliza uma venda
async def validating_information(current_user, payment_method: str, employee_operator_id: Optional[int] = None):

    from src.utils.sales_code_generator import gerar_codigo_venda

    # Carrinho do cliente
    from src.controllers.car.cart_control import CartManagerDB

    cart = CartManagerDB()

    try:

        # Inicializa admin e operador
        if hasattr(current_user, "username"):
            employee_operator_name = current_user.username
        elif hasattr(current_user, "nome"):
            employee_operator_name = current_user.username
        else:
            employee_operator_name = "Nome não disponível"

        # Verifica se o current_user é um funcionário
        is_employee = await Employees.filter(id=current_user.id).first()

        if is_employee and is_employee.usuario:
            # Busca o usuário pelo ID do relacionamento
            admin_user = await Usuario.get(id=is_employee.id)
            employee_operator_id = is_employee.id
            employee_operator_name = is_employee.nome
        else:
            admin_user = current_user
            employee_operator_id = None

        # Se foi passado employee_operator_id (admin vendendo para funcionário)
        extra_employee = None
        if employee_operator_id:
            extra_employee = await Employees.filter(id=employee_operator_id, usuario=admin_user.id).first()

        if extra_employee:
            employee_operator_id = extra_employee.id
            employee_operator_name = extra_employee.nome
        else:
            return {"status": False, "message": "Funcionário não encontrado"}

        # Lista produtos do carrinho do admin/dono
        products = await cart.listar_produtos(admin_user.id)

        if not products:
            return {"success": False, "data": None, "error": "Carrinho vazio"}

        if products:
            sale_total = 0.0
            sale_details = []
            for prod in products:
                sale_total += prod.price_total
                sale_details.append(
                    {
                        "product_id": prod.product_id,
                        "product_name": prod.product_name,
                        "quantity": prod.quantity,
                        "unit_price": prod.price,
                    }
                )

            # Gerando codigo de venda e nota de compra
            sale_code = gerar_codigo_venda()
            invoice = []
            for prod in sale_details:
                checkout = Checkout(
                    user_id=admin_user.id,
                    product_name=prod["product_name"],
                    produto_id=prod["product_id"],
                    quantity=prod["quantity"],
                    total_price=prod["quantity"] * prod["unit_price"],  # ✅ corrigido
                    lucro_total=0.0,
                    payment_method=payment_method.upper(),
                    funcionario_id=employee_operator_id,
                    funcionario_nome=employee_operator_name,
                    sale_code=sale_code,
                )
                # Nota fiscal
                coupon = await checkout.process_sale(
                    current_user=admin_user,
                    product_code=str(prod["product_id"]),
                    quantity=prod["quantity"],
                    payment_method=payment_method.upper(),
                    funcionario_id=employee_operator_id,
                )

                if coupon:
                    invoice.append(coupon)

                else:
                    raise Exception(
                        {
                            'message': 'O objeto coupon neste momento é None verifique no arquivo controller/sales.py',
                            'tipo': type(invoice),
                            'local': invoice if invoice is None else 'invoice esta com erros',
                        }
                    )
            # Limpa o carrinho do admin e gera relatório
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
                },
                "error": None,
            }

    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}
