# Main.py
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise

from src.conf.database import TORTOISE_ORM, print_database_info
from src.controllers.payments.partial.views_depts import ViewsAllDepts

# LOGS
from src.logs.infos import LOGGER
from src.routes.__init__ import *
from src.utils.dados_teste import create_mock_data_and_sell_all_stock


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    load_dotenv()

    # Inicializa banco de dados
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    LOGGER.info('✅ Banco de dados iniciado e tabelas criadas!')
    # await create_mock_data_and_sell_all_stock()

    # await print_database_info()

    yield

    await Tortoise.close_connections()
    LOGGER.info('🧱 Banco de dados encerrado com sucesso.')


class Server:
    def __init__(self):
        self.api = FastAPI(
            title='PDV API', version='1.0.0', debug=True, lifespan=lifespan
        )

        self.setup_middlewares()
        self.start_routes()

    def setup_middlewares(self):
        """Configura CORS."""
        origins = [
            'http://127.0.0.1:5000',
            'https://nahtec.com.br',
            'https://nahtec.com.br/pdv',
        ]

        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    def start_routes(self):
        """Registra as rotas principais da aplicação."""
        self.api.include_router(auth)
        self.api.include_router(Funcionários)
        self.api.include_router(clientes)
        self.api.include_router(produtos)
        self.api.include_router(carrinho)
        self.api.include_router(fornecedor)
        self.api.include_router(tickets)
        self.api.include_router(dashboard)
        self.api.include_router(paymente)
        self.api.include_router(delivery)
        self.api.include_router(marketplace)
        self.api.include_router(my_inventario)

        from src.routes.caixa.start_router import checkout

        self.api.include_router(checkout)

    def run(self, host: str = '0.0.0.0', port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run(
            'Main:app', host=host, port=port, reload=True, log_level='info'
        )


app = Server().api

if __name__ == '__main__':
    Server().run()
