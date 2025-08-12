from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

# Importa o modelo para registrar na metadata do SQLModel
from src.conf.database import create_db_and_tables, engine
from src.routes.cliente_cnpj import ConsultaRoute

# Rotas
from src.routes.login import Login
from src.routes.products import products_router
from src.routes.registre import RegisterRoute
from src.routes.updates import AllDatas
from src.routes.account.account import RegisteEmpreg

# Dados de teste mocados
from src.utils.dados_teste import create_mock_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Coisas ao iniciar a aplicação
    load_dotenv()
    create_db_and_tables()
    print('Banco de dados iniciado e tabelas criadas!')

    # Iniciando dodos mocados para desenvolvimento
    create_mock_data()

    yield

    # Coisas ao finalizar a aplicação
    print('Fim da aplicação')
    engine.dispose()


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
        
        # Rota para cadastra fucionarios
        funcs_router = RegisteEmpreg()
        self.api.include_router(funcs_router.router)

        # Rota de consulta
        consultaroute = ConsultaRoute()
        self.api.include_router(consultaroute.router)

        # Rota de cadastro de produtos
        self.api.include_router(products_router)
        


        # Rota de visualização dos dados em tempo real.
        route_update_dash = AllDatas()
        self.api.include_router(route_update_dash.allDatas)

    def run(self, host: str = '127.0.0.1', port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run('Main:app', host=host, port=port, reload=True)


# Variável global para o Uvicorn
app = Server().api

if __name__ == '__main__':
    Server().run()
