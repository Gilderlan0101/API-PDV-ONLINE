"""
Módulo: login.py
Descrição: Define as rotas de login da aplicação FastAPI.

Este módulo contém a classe `Login` que encapsula:
- Criação do roteador APIRouter específico para login
- Definição da rota POST `/login`
- Validação dos dados de entrada usando `LoginSchema`
- Verificação básica de credenciais (mock/dados de teste)

Fluxo de funcionamento:
1. O cliente envia um POST para `/login` com `email` e `pwd` no corpo da requisição.
2. O FastAPI valida automaticamente os dados recebidos usando `LoginSchema`.
3. O servidor verifica se as credenciais são válidas (neste exemplo, usando um dicionário estático).
4. Retorna um JSON com o status do login.

OBS: Este exemplo ainda não acessa banco de dados real e não faz hashing de senha.
"""

from fastapi import APIRouter, HTTPException, status
from ..schemas.schema_user import LoginSchema

# Dados mock (para teste de login sem banco)
data = {'email': 'exemplo@gmail.com', 'pwd': '12345'}


class Login:
    def __init__(self):
        """Inicializa a classe de rotas de login."""
        self.loginRT = APIRouter()
        self.startup_route()  # Registra as rotas no APIRouter

    def startup_route(self):
        """Define e registra as rotas relacionadas ao login."""

        @self.loginRT.post('/login')
        async def login(user: LoginSchema):
            """
            Rota de login do usuário.

            Args:
                user (LoginSchema): Objeto Pydantic com os campos `email` e `pwd`.

            Returns:
                dict: Status da autenticação.
            """
            try:
                # Verifica credenciais mock
                if user.email == data.get('email') and user.pwd == data.get(
                    'pwd'
                ):
                    return {
                        'status': 200,
                        'message': 'Login realizado com sucesso',
                    }

                # Caso contrário, retorna erro genérico
                return {'status': 401, 'message': 'Credenciais inválidas'}

            except Exception as e:
                # Captura qualquer erro inesperado
                return {'status': 500, 'error': str(e)}
