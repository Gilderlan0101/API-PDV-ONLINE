from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select
from passlib.hash import bcrypt

from ..conf.database import engine
from ..model.user.users import Usuario
from ..schemas.schema_user import LoginSchema


class Login:
    def __init__(self):
        """Inicializa a classe de rotas de login."""
        self.loginRT = APIRouter(
            prefix="/auth",  # Prefixo para todas as rotas deste router
            tags=["Autenticação"]  # Nome do grupo no /docs
        )
        self.startup_route()

    def startup_route(self):
        """Define e registra as rotas relacionadas ao login."""

        @self.loginRT.post('/login', status_code=status.HTTP_200_OK)
        async def login(user: LoginSchema):
            """
            Rota de login do usuário.
            Verifica email e senha no banco de dados.
            """
            with Session(engine) as session:
                # 1️⃣ Buscar usuário pelo e-mail
                db_user = session.exec(
                    select(Usuario).where(Usuario.email == user.email)
                ).first()

                if not db_user:
                    raise HTTPException(
                        status_code=401,
                        detail='Credenciais inválidas (email)',
                    )

                # 2️⃣ Verificar senha com bcrypt
                if not bcrypt.verify(user.pwd, db_user.password):
                    raise HTTPException(
                        status_code=401,
                        detail='Credenciais inválidas (senha)',
                    )

                # 3️⃣ Retornar dados básicos (sem senha)
                return {
                    'id': db_user.id,
                    'username': db_user.username,
                    'email': db_user.email,
                    'empresa': db_user.company_name,
                    'message': 'Login realizado com sucesso',
                }
