from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

# Autenticação
from ..auth.auth_jwt import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from ..conf.database import engine
from ..model.user import Usuario
from ..model.employee import Employees  # ← IMPORTANTE
from ..schemas.schema_user import TokenSchema


class Login:
    def __init__(self):
        """Inicializa a classe de rotas de login."""
        self.loginRT = APIRouter(
            prefix='/auth',
            tags=['Autenticação'],
        )
        self.startup_route()

    def startup_route(self):
        """Define e registra as rotas relacionadas ao login."""

        @self.loginRT.post(
            '/login',
            status_code=status.HTTP_200_OK,
            response_model=TokenSchema,
        )
        async def login(user: OAuth2PasswordRequestForm = Depends()):
            """
            Rota de login do usuário ou funcionário.
            Verifica email e senha no banco de dados.
            """
            with Session(engine) as session:
                # 1️ Tentar login como usuário principal
                db_user = session.exec(
                    select(Usuario).where(Usuario.email == user.username)
                ).first()

                if db_user:
                    if not verify_password(user.password, db_user.password):
                        raise HTTPException(
                            status_code=401,
                            detail='Credenciais inválidas (senha)',
                        )

                    return {
                        'id': db_user.id,
                        'username': db_user.username,
                        'email': db_user.email,
                        'empresa': db_user.company_name,
                        'tipo': 'usuario',
                        'message': 'Login realizado com sucesso',
                        'access_token': create_access_token(str(db_user.id)),
                        'refresh_token': create_refresh_token(str(db_user.id)),
                        'token_type': 'bearer',
                    }

               # 2️ Tentar login como funcionário
            employee = session.exec(
                select(Employees).where(Employees.email == user.username)
            ).first()
            
            if employee:
                # Verifica senha (já usando hash se estiver armazenada assim)
                if not verify_password(user.password, employee.senha):
                    raise HTTPException(
                        status_code=401,
                        detail='Credenciais inválidas (senha)',
                    )
            
                if not employee.ativo:
                    raise HTTPException(
                        status_code=403,
                        detail='Funcionário inativo. Entre em contato com a empresa.',
                    )
            
                return {
                    'id': employee.id,
                    'username': employee.nome,
                    'email': employee.email,
                    'empresa': employee.usuario.company_name if employee.usuario else None,
                    'tipo': 'funcionario',
                    'message': 'Login realizado com sucesso',
                    'access_token': create_access_token(str(employee.id)),
                    'refresh_token': create_refresh_token(str(employee.id)),
                    'token_type': 'bearer',
                }
            