# Main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from tortoise import Tortoise
from dotenv import load_dotenv
import uvicorn

from src.conf.database import TORTOISE_ORM, print_database_info
from src.routes.__init__ import *

from src.utils.dados_teste import create_mock_data_and_sell_all_stock

# LOGS
from src.logs.infos import LOGGER

from src.controllers.payments.partial.views_depts import ViewsAllDepts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    load_dotenv()

    # Inicializa banco de dados
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    LOGGER.info("✅ Banco de dados iniciado e tabelas criadas!")
    # await create_mock_data_and_sell_all_stock()

    # await print_database_info()

    yield

    await Tortoise.close_connections()
    LOGGER.info("🧱 Banco de dados encerrado com sucesso.")


class Server:
    def __init__(self):
        self.api = FastAPI(title="PDV API", version="1.0.0", debug=True, lifespan=lifespan, swagger_ui_init_oauth=None, docs_url=None)

        self.setup_middlewares()
        self.start_routes()

    def setup_middlewares(self):
        """Configura CORS."""
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:5000",
            "https://front-end-pdv.onrender.com",
            "https://api-pdv-online.onrender.com",
            "https://nahtec.com.br",
            "https://nahtec.com.br/pdv",
        ]

        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,  # 🔥 IMPORTANTE: Permitir cookies
            allow_methods=["*"],
            allow_headers=["*"],
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

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run("Main:app", host=host, port=port, reload=True, log_level="info")


app = Server().api

if __name__ == "__main__":
    Server().run()
