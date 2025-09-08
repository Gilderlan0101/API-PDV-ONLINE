from fastapi import APIRouter
from src.routes.cliente_cnpj import ConsultaRoute
from src.routes.login import Login
from src.routes.fornecedor.registre_fornecedor import router as fornecedores_rt
from src.routes.car import cart_router
from src.routes.registre import registerRT
from src.routes.updates import allDatas
from src.routes.account.account import registe_empreg
from src.routes.customer.customer_registration import customers
from src.routes.caixa.operador_caixa import operador
from src.routes.car.pdv import router as result_sales

from src.routes.products.buscar_prod import buscar_produtos
from src.routes.products.list import list_products as list_router
from src.routes.products.create import router as create_products
from src.routes.products.update import router as updates_products
from src.routes.products.delete import router as delete_products
from src.routes.products.upload_img import router as upload_img
from src.routes.products.ticket import router as ticket_prods
from src.routes.products.sales import router as sales
from src.routes.products.cancel_sale import router as cancel_sales


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
Funcionários.include_router(registe_empreg, prefix="/funcionarios", tags=["Funcionários"])

clientes = APIRouter(
    tags=["Consultas"],
    responses={404: {"description": "Não encontrado"}},
)

# Consulta de clientes
consultaroute = ConsultaRoute()
clientes.include_router(consultaroute.router, prefix="/clientes", tags=["Consultas"])
clientes.include_router(customers)
# Produtos
produtos = APIRouter(
    tags=["Produtos"],
    responses={404: {"description": "Não encontrado"}},
)

produtos.include_router(upload_img)
produtos.include_router(buscar_produtos)
produtos.include_router(list_router)
produtos.include_router(create_products)
produtos.include_router(updates_products)
produtos.include_router(delete_products)

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
