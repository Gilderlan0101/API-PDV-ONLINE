from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

# Autenticação
from src.auth.auth_jwt import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from src.model.user import Usuario
from src.model.employee import Employees  # ← Funcionários
from src.schemas.schema_user import TokenSchema

from src.model.membros import Membro


class Login:
    def __init__(self):
        """Inicializa a classe de rotas de login."""
        self.loginRT = APIRouter(
            prefix="/auth",
            tags=["Autenticação"],
        )
        self.startup_route()

    def startup_route(self):
        """Define e registra as rotas relacionadas ao login."""

        @self.loginRT.post(
            "/login",
            status_code=status.HTTP_200_OK,
            response_model=TokenSchema,
        )
        async def login(user: OAuth2PasswordRequestForm = Depends()):
            """
            Rota de login do usuário ou funcionário.
            Verifica email e senha no banco de dados.
            """

            # 🔹 1) Login como usuário principal
            db_user = await Usuario.get_or_none(email=user.username)
            if db_user:
                if not verify_password(user.password, db_user.password):
                    raise HTTPException(
                        status_code=401,
                        detail="Credenciais inválidas (senha)",
                    )

                return {
                    "id": db_user.id,
                    "username": db_user.username,
                    "email": db_user.email,
                    "empresa": db_user.company_name,
                    "tipo": "admin",
                    "message": "Login realizado com sucesso",
                    "access_token": create_access_token(str(db_user.id)),
                    "refresh_token": create_refresh_token(str(db_user.id)),
                    "token_type": "bearer",
                }

            # 🔹 2) Login como funcionário
            employee = await Employees.get_or_none(email=user.username).select_related("usuario")

            if employee:
                if not verify_password(user.password, employee.senha):
                    raise HTTPException(
                        status_code=401,
                        detail="Credenciais inválidas (senha)",
                    )

                if not employee.ativo:
                    raise HTTPException(
                        status_code=403,
                        detail="Funcionário inativo. Entre em contato com a empresa.",
                    )

                return {
                    "id": employee.id,
                    "username": employee.nome,
                    "email": employee.email,
                    "empresa": (employee.usuario.company_name if employee.usuario else None),
                    "tipo": "funcionario",
                    "message": "Login realizado com sucesso",
                    "access_token": create_access_token(str(employee.id)),
                    "refresh_token": create_refresh_token(str(employee.id)),
                    "token_type": "bearer",
                }

            # 🔹 3) Login como membro
            membros = await Membro.get_or_none(email=user.username).select_related("usuario")

            if membros:
                if not verify_password(user.password, membros.senha):
                    raise HTTPException(
                        status_code=401,
                        detail="Credenciais inválidas (senha)",
                    )

                if not membros.ativo:
                    raise HTTPException(
                        status_code=403,
                        detail="Funcionário inativo. Entre em contato com a empresa.",
                    )

                return {
                    "id": membros.id,
                    "username": membros.nome,
                    "email": membros.email,
                    "empresa": (membros.usuario.company_name if membros.usuario else None),
                    "tipo": "funcionario",
                    "message": "Login realizado com sucesso",
                    "access_token": create_access_token(str(membros.id)),
                    "refresh_token": create_refresh_token(str(membros.id)),
                    "token_type": "bearer",
                }

            raise HTTPException(
                status_code=401,
                detail="Credenciais inválidas (usuário/funcionário não encontrado)",
            )
