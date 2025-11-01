from contextlib import asynccontextmanager
from tortoise import Tortoise
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Importa o modelo para registrar na metadata do SQLModel
from src.conf.database import TORTOISE_ORM

# Rotas
from src.routes.__init__ import *

# from src.routes.relatorio.relatorio import router


# Dados de teste mocados
from src.utils.dados_teste import create_mock_data_and_sell_all_stock

# Configuração do cors
from fastapi.middleware.cors import CORSMiddleware


######################################################################
# Testando dados para admin
# from src.controllers.user.system_users import LoginInSystem, SystemUser

# from src.controllers.products.monitoring_products import ProductInfo
# from src.controllers.payments.partial import PartialPayment, Person
# from src.controllers.products.products_infors import Products
from src.controllers.caixa.cash_reports import CashReportController

from src.controllers.delivery.delivery_controller import CreateDelivery
from src.controllers.delivery.delivery_reports import gerenciagelivery
from src.controllers.payments.pix import PixService
from src.utils.get_produtos_user import deep_search
from src.controllers.marketplace.product_search_service import CustomerMarketplace
from src.utils.load_images import load_imgs
from src.core.cache import check_redis_connection

######################################################################


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carrega variáveis de ambiente
    load_dotenv()

    # Inicializa banco de dados e gera tabelas
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    print("Banco de dados iniciado e tabelas criadas!")

    # Cria dados mock
    await create_mock_data_and_sell_all_stock()

    yield

    # Fecha conexões
    await Tortoise.close_connections()
    print("Fim da aplicação")


class Server:
    def __init__(self):
        self.api = FastAPI(
            title='PDV API',
            config=TORTOISE_ORM,
            generate_schemas=True,
            add_exception_handlers=True,
            description="""
            API para gerenciamento de um sistema PDV (Ponto de Venda) teste.

            ### Funcionalidades:
            - Autenticação e cadastro de usuários
            - Cadastro e gestão de funcionários
            - Cadastro, listagem e atualização de produtos
            - Gestão de carrinho de compras
            - Finalização e cancelamento de vendas
            - Consultas de clientes via CNPJ
            - Visualização de dados em tempo real

            ### Observações:
            - Todas rotas requerem autenticação exceto login e registro
            - Documentação interativa disponível no `/docs`
            """,
            version='1.0.0',
            debug=True,
            lifespan=lifespan,
            contact={
                "name": "Gilderlan Silva",
                "email": "dacruzgg01@gmail.com",
                "url": "https://gilderlan-dev-d8xp.onrender.com/Gilderlan.Dev/",
            },
            license_info={
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT",
            },
        )
        self.start_routes()
        self.teste()

        # CONFIGURAÇÃO CORS ATUALIZADA
        origins = [
            "http://localhost:5000",  # Flask development server
            "http://127.0.0.1:5000",  # Flask development server
            "http://localhost:8080",  # Vue.js/React development
            "http://127.0.0.1:8080",  # Vue.js/React development
            "http://localhost:3000",  # React development
            "http://127.0.0.1:3000",  # React development
            "http://localhost:5173",  # Vite development
            "http://127.0.0.1:5173",  # Vite development
            "http://localhost:8000",  # FastAPI itself
            "http://127.0.0.1:8000",  # FastAPI itself
            "https://front-end-pdv.onrender.com",  # Frontend Flask
            "https://api-pdv-online.onrender.com",  # Backend FastAPI
            "https://nahtec.com.br",  # Rota princial onde vamos subir o app e api
            "https://nahtec.com.br/pdv",  # Apenas para teste
        ]

        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],  # permite POST, GET, OPTIONS etc.
            allow_headers=["*"],  # permite Content-Type, Authorization etc.
        )

    def start_routes(self):
        """Inclui todas as rotas da API organizadas por funcionalidade e tag."""

        self.api.include_router(auth)
        self.api.include_router(Funcionários)
        self.api.include_router(clientes)
        self.api.include_router(produtos)
        self.api.include_router(carrinho)
        self.api.include_router(fornecedor)
        self.api.include_router(tickets)
        self.api.include_router(caixa)
        self.api.include_router(dashboard)
        self.api.include_router(paymente)
        self.api.include_router(delivery)
        self.api.include_router(marketplace)

    def run(self, host: str = '0.0.0.0', port: int = 8000):
        """Inicia o sevidor Uvicorn."""
        uvicorn.run('Main:app', host=host, port=port, reload=True, log_level="debug")

    async def teste(self):
        return await check_redis_connection()

# Variavel global para o Uvicorn
app = Server().api

if __name__ == '__main__':
    Server().run()
