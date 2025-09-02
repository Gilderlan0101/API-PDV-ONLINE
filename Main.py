from contextlib import asynccontextmanager
from tortoise import Tortoise
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

# Importa o modelo para registrar na metadata do SQLModel
from src.conf.database import TORTOISE_ORM

# Rotas
from src.routes.cliente_cnpj import ConsultaRoute
from src.routes.login import Login
from src.routes.products import products_router, fornecedores, ticket_prods
from src.routes.car import cart_router
from src.routes.registre import registerRT
from src.routes.updates import allDatas
from src.routes.account.account import registe_empreg
from src.routes.customer.customer_registration import customers
from src.routes.cadastros.operador_caixa import operador
# from src.routes.relatorio.relatorio import router


# Dados de teste mocados
from src.utils.dados_teste import create_mock_data
# Configuração do cors
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    """
    load_dotenv()
    
    # Inicializa Tortoise ORM
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()  # cria tabelas se necessário
    print('Banco de dados iniciado e tabelas criadas!')

    # Popula dados de teste
    await create_mock_data()

    yield

    # Fecha conexões
    await Tortoise.close_connections()
    print('Fim da aplicação')

class Server:
    def __init__(self):
        self.api = FastAPI(
            title='PDV API',
            config=TORTOISE_ORM,
            generate_schemas=True,
            add_exception_handlers=True,
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
        
        # CONFIGURAÇÃO CORS ATUALIZADA
        origins = [
             "http://localhost:5000",      # Flask development server
             "http://127.0.0.1:5000",      # Flask development server
             "http://localhost:8080",      # Vue.js/React development
             "http://127.0.0.1:8080",      # Vue.js/React development
             "http://localhost:3000",      # React development
             "http://127.0.0.1:3000",      # React development
             "http://localhost:5173",      # Vite development
             "http://127.0.0.1:5173",      # Vite development
             "http://localhost:8000",      # FastAPI itself
             "http://127.0.0.1:8000",        # FastAPI itself
             "https://api-pdv-online.onrender.com/"
         ]
        
        
        self.api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
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
        
        self.api.include_router(
            registerRT, prefix="/auth", tags=["Autenticação"]
        )

        # Cadastro de funcionários
        
        self.api.include_router(
            registe_empreg, prefix="/funcionarios", tags=["Funcionários"]
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
        
        self.api.include_router(fornecedores)
        self.api.include_router(ticket_prods)
        
        self.api.include_router(operador)


        # Visualização de dados em tempo real
        
        self.api.include_router(
            allDatas, prefix="/dashboard", tags=["Dashboard"]
        )
        
        # Cadastra e visualiza dados de clientes
        self.api.include_router(customers)

    def run(self, host: str = '127.0.0.1', port: int = 8000):
        """Inicia o servidor Uvicorn."""
        uvicorn.run('Main:app', host=host, port=port, reload=True, log_level="debug")



# Variável global para o Uvicorn
app = Server().api

if __name__ == '__main__':
    Server().run()