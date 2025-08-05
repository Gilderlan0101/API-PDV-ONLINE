from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
import uvicorn

# Importa o modelo para registrar na metadata do SQLModel
from .src.conf.database import create_db_and_tables

# Rotas
from .src.routes.login import Login
from .src.routes.registre import RegisterRoute
from .src.routes.cliente_cnpj import ConsultaRoute
from .src.routes.products import Product


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Coisas ao iniciar a aplicação
    load_dotenv()
    create_db_and_tables()
    print('Banco de dados iniciado e tabelas criadas!')

    yield

    # Coisas ao finalizar a aplicação
    print('Fim da aplicação')


class Server:
    def __init__(self):
        self.api = FastAPI(
            title='PDV API',
            description='API para o sistema PDV',
            version='1.0.0',
            debug=True,
            lifespan=lifespan,
        )
        self.start_routes()

    def start_routes(self):

        # Rota de login
        login_route = Login()
        self.api.include_router(login_route.loginRT)

        # Rota de cadastro
        register_route = RegisterRoute()
        self.api.include_router(register_route.registerRT)

        # Rota de consulta
        consultaroute = ConsultaRoute()
        self.api.include_router(consultaroute.router)

        # Rota de cadastro de produtos
        route_product = Product()
        self.api.include_router(route_product.router)

    def run(self, host: str = '127.0.0.1', port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run('Main:app', host=host, port=port, reload=True)


# Variável global para o Uvicorn
app = Server().api

if __name__ == '__main__':
    Server().run()
