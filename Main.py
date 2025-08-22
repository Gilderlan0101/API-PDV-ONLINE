from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

# Importa o modelo para registrar na metadata do SQLModel
from src.conf.database import create_db_and_tables, engine

# Rotas
from src.routes.cliente_cnpj import ConsultaRoute
from src.routes.login import Login
from src.routes.products import products_router
from src.routes.car import cart_router
from src.routes.registre import RegisterRoute
from src.routes.updates import AllDatas
from src.routes.account.account import RegisteEmpreg

# Dados de teste mocados
from src.utils.dados_teste import create_mock_data
# Configuração do cors
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.

    - Carrega variáveis de ambiente
    - Cria banco e tabelas
    - Popula dados de teste
    """
    load_dotenv()
    create_db_and_tables()
    print('Banco de dados iniciado e tabelas criadas!')

    # Dados de teste para desenvolvimento
    create_mock_data()

    yield

    # Finalização da aplicação
    print('Fim da aplicação')
    engine.dispose()


class Server:
    def __init__(self):
        self.api = FastAPI(
            title='PDV API',
            description="""
            API para gerenciamento de um sistema PDV (Ponto de Venda).

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
        
        origins = [
            "http://localhost:8080",  # sua aplicação frontend
            "http://127.0.0.1:8080",
            "http://127.0.0.1:5000"
        ]
        
        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,  # ou ["*"] para liberar tudo
            allow_credentials=True,
            allow_methods=["*"],    # permite POST, GET, OPTIONS etc.
            allow_headers=["*"],    # permite Content-Type, Authorization etc.
        )


    def start_routes(self):
        """Inclui todas as rotas da API organizadas por funcionalidade e tag."""

        # Login
        login_route = Login()
        self.api.include_router(
            login_route.loginRT, tags=["Autenticação"]
        )

        # Cadastro de usuário
        register_route = RegisterRoute()
        self.api.include_router(
            register_route.registerRT, prefix="/auth", tags=["Autenticação"]
        )

        # Cadastro de funcionários
        funcs_router = RegisteEmpreg()
        self.api.include_router(
            funcs_router.router, prefix="/funcionarios", tags=["Funcionários"]
        )

        # Consulta de clientes
        consultaroute = ConsultaRoute()
        self.api.include_router(
            consultaroute.router, prefix="/clientes", tags=["Consultas"]
        )

        # Produtos
        self.api.include_router(products_router)

        # Carrinho
        self.api.include_router(cart_router)

        # Visualização de dados em tempo real
        route_update_dash = AllDatas()
        self.api.include_router(
            route_update_dash.allDatas, prefix="/dashboard", tags=["Dashboard"]
        )

    def run(self, host: str = '127.0.0.1', port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run('Main:app', host=host, port=port, reload=True)


# Variável global para o Uvicorn
app = Server().api

if __name__ == '__main__':
    Server().run()
