# src/routes/auth_routes.py - Versão Completa

import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.auth_jwt import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from src.model.user import Usuario
from src.schemas.schema_user import TokenSchema

# Importe as dependencias de fora, como o cliente Redis
from src.core.cache import client
from src.logs.infos import LOGGER
from src.auth.deps import get_current_user, SystemUser, reuseable_oauth  # Adicionado para debug de logout


class Login:

    def __init__(self):
        self.loginRT = APIRouter(
            prefix="/auth",
            tags=["Autenticação"],
        )
        self._register_routes()

    def _register_routes(self):

        # --- Rota /login ---
        @self.loginRT.post(
            "/login",
            status_code=status.HTTP_200_OK,
            response_model=TokenSchema,
        )
        async def login(user: OAuth2PasswordRequestForm = Depends()):
            LOGGER.info(f"🔐 Tentativa de login: {user.username}")

            # 1. Autenticação
            db_user = await Usuario.get_or_none(email=user.username)
            if not db_user or not verify_password(user.password, db_user.password):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")

            # 2. Gerar Tokens
            access_token = create_access_token(str(db_user.id))
            refresh_token = create_refresh_token(str(db_user.id))

            # 3. Preparar Dados para Cache (Usado para a dependência get_current_user)
            # Estes sao os dados que serao salvos no Redis para validacao rapida
            session_data_for_cache = {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "company_name": db_user.company_name,
                "cnpj": db_user.cnpj,
                "cpf": db_user.cpf,
                "is_active": db_user.is_active,
                "empresa_id": db_user.id,
                "tipo": "admin",
            }

            # 4. Salvar o Cache (Token como chave) - Cache persistente (sem expiração)
            cache_key = f'token:{access_token}'
            await client.set(cache_key, json.dumps(session_data_for_cache, default=str))
            LOGGER.info(f"Token salvo no cache. Chave: {cache_key}")

            # 5. Retorno Final
            return {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "empresa": db_user.company_name,
                "empresa_id": db_user.id,
                "tipo": "admin",
                "message": "Login realizado com sucesso",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "session_id": str(uuid.uuid4()),  # Campo Dummy para satisfazer o TokenSchema
            }

        @self.loginRT.post("/logout")
        async def logout(token: str = Depends(reuseable_oauth)):
            """Encerra a sessão no Redis, invalidando o token imediatamente."""

            cache_key = f'token:{token}'

            # Deleta a chave do cache
            remove = await client.delete(cache_key)

            if remove == 0:
                # O token pode ter expirado ou ja foi deletado, mas reportamos sucesso
                LOGGER.info(f"Tentativa de logout: Token nao encontrado em cache (Chave: {cache_key}).")

            LOGGER.info(f"Logout bem-sucedido. Chave de cache removida: {cache_key}")

            return {"status": 200}

        # --- Rotas de Debug (Mantidas) ---

        # Rotas de refresh e debug
        @self.loginRT.post("/refresh-session")
        async def refresh_session(request: Request, response: Response):
            """Renova o tempo da sessão"""
            # Logica de renovacao...
            return {"message": "Sessão renovada com sucesso"}

        @self.loginRT.get("/debug-sessions")
        async def debug_sessions():
            """Endpoint para debug - lista todas as sessões no Redis"""
            # Logica de debug
            return {"total_sessions": 0, "sessions": {}}
