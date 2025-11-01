# __init__.py inicia as rotas
from fastapi import APIRouter
from src.routes.cliente_cnpj import ConsultaRoute
from src.routes.login import Login
from src.routes.fornecedor.registre_fornecedor import router as fornecedores_rt
from src.routes.car import cart_router
from src.routes.registre import registerRT
from src.routes.updates import allDatas

# Funcionarios
from src.routes.account.account import employees_router as account
from src.routes.account.employee_list import employees_router
from src.routes.account.employee_edit import employees_router as edit_employees

# Cadastro de clientes
from src.routes.customer.customer_registration import customers
from src.routes.customer.registre_customer_partial import customers as registre_user_partial


# Metodos de pagamentos
from src.routes.payments.partial import partial as payment_partial
from src.routes.payments.pix import router as payment_pix

from src.routes.caixa.operador_caixa import operador
from src.routes.caixa.box_closing import operador

from src.routes.car.pdv import router as result_sales

# Rotas relacionadas a produtos
from src.routes.products.buscar_prod import buscar_produtos
from src.routes.products.list import list_products as list_router
from src.routes.products.product_information import list_products as product_info
from src.routes.products.create import router as create_products
from src.routes.products.update import router as updates_products
from src.routes.products.delete import router as delete_products
from src.routes.products.upload_img import router as upload_img
from src.routes.products.ticket import router as ticket_prods
from src.routes.products.sales import router as sales
from src.routes.products.cancel_sale import router as cancel_sales
from src.routes.products.deep_infos import product_deep_infos

from src.routes.user.clientes import router as system_user

# Delivery
from src.routes.delivery.create_delivery import delivery_router

# marketplace
from src.routes.marketplace.marketplace_between_customers import marketplace

# Inventario
from src.routes.products.inventario.stock_entry_controller import inventory_router as stoke
from src.routes.products.inventario.label_generator import inventory_router as label
from src.routes.products.inventario.stock_exit_controller import inventory_router as exit

auth = APIRouter(
    tags=["Autenticação"],
    responses={404: {"description": "Não encontrado"}},
)


# Login
login = Login()

auth.include_router(login.loginRT)
# Cadastro de usuário
auth.include_router(registerRT, prefix="/auth", tags=["Autenticação"])

Funcionários = APIRouter(
    tags=["Funcionários"],
    responses={404: {"description": "Não encontrado"}},
)

# Cadastro de funcionários
Funcionários.include_router(employees_router, prefix="/funcionarios", tags=["Funcionários"])
Funcionários.include_router(edit_employees, prefix="/funcionarios", tags=["Funcionários"])
Funcionários.include_router(account, prefix="/funcionarios", tags=["Funcionários"])


clientes = APIRouter(
    tags=["Consultas"],
    responses={404: {"description": "Não encontrado"}},
)

# Consulta de clientes
consultaroute = ConsultaRoute()
clientes.include_router(consultaroute.router, prefix="/clientes", tags=["Consultas"])
clientes.include_router(customers)
clientes.include_router(registre_user_partial)


# Produtos
produtos = APIRouter(
    tags=["Produtos"],
    responses={404: {"description": "Não encontrado"}},
)

produtos.include_router(upload_img)
produtos.include_router(buscar_produtos)
produtos.include_router(list_router)
produtos.include_router(product_info)
produtos.include_router(create_products)
produtos.include_router(updates_products)
produtos.include_router(delete_products)
produtos.include_router(product_deep_infos)


# Carrinho
carrinho = APIRouter(
    tags=["Carrinho"],
    responses={404: {"description": "Não encontrado"}},
)
carrinho.include_router(cart_router)
carrinho.include_router(sales)
carrinho.include_router(cancel_sales)


# Fonecedor
fornecedor = APIRouter(
    tags=["Fonecedor"],
    responses={404: {"description": "Não encontrado"}},
)
fornecedor.include_router(fornecedores_rt)

# Tickets
tickets = APIRouter(
    tags=["Tickets"],
    responses={404: {"description": "Não encontrado"}},
)

tickets.include_router(ticket_prods)

# Caixa
caixa = APIRouter(
    tags=["Caixa"],
    responses={404: {"description": "Não encontrado"}},
)
caixa.include_router(operador)

# Visualização de dados em tempo real dashboard
dashboard = APIRouter(
    tags=["dashboard"],
    responses={404: {"description": "Não encontrado"}},
)

dashboard.include_router(allDatas, prefix="/dashboard", tags=["Dashboard"])
dashboard.include_router(result_sales)

# Visualização de dados em tempo real dashboard
system_ = APIRouter(
    tags=["system_user"],
    responses={404: {"description": "Não encontrado"}},
)

dashboard.include_router(system_user)


# Metodos de pagamento
paymente = APIRouter(
    tags=['Pagamentos'],
    responses={404: {'description': 'Não encontrado'}},
)

paymente.include_router(payment_partial)
paymente.include_router(payment_pix)
paymente.include_router(delivery_router)


delivery = APIRouter(
    tags=['Delivery'],
)

delivery.include_router(delivery_router)

marketplace_prods = APIRouter(tags=['marketplace'])
marketplace_prods.include_router(marketplace)

my_inventario = APIRouter()
my_inventario.include_router(stoke)
my_inventario.include_router(label)
my_inventario.include_router(exit)