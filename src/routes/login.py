# src/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.auth_jwt import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from src.model.user import Usuario
from src.model.employee import Employees
from src.model.membros import Membro
from src.schemas.schema_user import TokenSchema
from src.core.session_manager import session_manager, get_session


class Login:
    def __init__(self):
        self.loginRT = APIRouter(
            prefix="/auth",
            tags=["Autenticação"],
        )
        self._register_routes()

    def _register_routes(self):
        @self.loginRT.post(
            "/login",
            status_code=status.HTTP_200_OK,
            response_model=TokenSchema,
        )
        async def login(request: Request, response: Response, user: OAuth2PasswordRequestForm = Depends()):
            print(f"🔐 Tentativa de login: {user.username}")

            # 1️⃣ Login como Usuário principal (Dono da empresa)
            db_user = await Usuario.get_or_none(email=user.username)
            if db_user:
                if not verify_password(user.password, db_user.password):
                    raise HTTPException(status_code=401, detail="Credenciais inválidas")

                # 🎯 Cria sessão no Redis com dados importantes
                session_data = {
                    "user_id": db_user.id,
                    "empresa_id": db_user.id,  # Usuário é dono
                    "tipo": "admin",
                    "username": db_user.username,
                    "email": db_user.email,
                    "company_name": db_user.company_name,
                    "access_token": create_access_token(str(db_user.id)),
                    "refresh_token": create_refresh_token(str(db_user.id)),
                    "logged_in": True,
                }

                session_id = session_manager.create_session(response, session_data)
                print(f"✅ Sessão criada no Redis: {session_id}")

                return {
                    "id": db_user.id,
                    "username": db_user.username,
                    "email": db_user.email,
                    "empresa": db_user.company_name,
                    "empresa_id": db_user.id,
                    "tipo": "admin",
                    "message": "Login realizado com sucesso",
                    "access_token": create_access_token(str(db_user.id)),
                    "refresh_token": create_refresh_token(str(db_user.id)),
                    "token_type": "bearer",
                    "session_id": session_id,  # Para debug
                }

            # 2️⃣ Login como Funcionário
            employee = await Employees.get_or_none(email=user.username).select_related("usuario")
            if employee:
                if not verify_password(user.password, employee.senha):
                    raise HTTPException(status_code=401, detail="Credenciais inválidas")

                if not employee.ativo:
                    raise HTTPException(status_code=403, detail="Funcionário inativo.")

                if not employee.usuario:
                    raise HTTPException(status_code=403, detail="Funcionário não vinculado a uma empresa.")

                # 🎯 Cria sessão no Redis com dados importantes
                session_data = {
                    "employee_id": employee.id,
                    "user_id": employee.usuario_id,  # Para compatibilidade
                    "empresa_id": employee.usuario_id,  # ID da empresa do dono
                    "tipo": "funcionario",
                    "username": employee.nome,
                    "email": employee.email,
                    "company_name": employee.usuario.company_name,
                    "access_token": create_access_token(str(employee.id)),
                    "refresh_token": create_refresh_token(str(employee.id)),
                    "logged_in": True,
                }

                session_id = session_manager.create_session(response, session_data)
                print(f"✅ Sessão de funcionário criada no Redis: {session_id}")

                return {
                    "id": employee.id,
                    "username": employee.nome,
                    "email": employee.email,
                    "empresa": employee.usuario.company_name,
                    "empresa_id": employee.usuario_id,
                    "tipo": "funcionario",
                    "message": "Login realizado com sucesso",
                    "access_token": create_access_token(str(employee.id)),
                    "refresh_token": create_refresh_token(str(employee.id)),
                    "token_type": "bearer",
                    "session_id": session_id,  # Para debug
                }

            # 3️⃣ Nenhum usuário encontrado
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        @self.loginRT.get("/session")
        async def session_info(session: dict = Depends(get_session)):
            """Retorna informações da sessão atual do Redis"""
            return {"session": session, "session_keys": list(session.keys()) if session else []}

        @self.loginRT.post("/logout")
        async def logout(request: Request, response: Response):
            """Encerra a sessão no Redis"""
            session_manager.delete_session(request, response)
            return {"message": "Logout realizado com sucesso"}

        @self.loginRT.post("/refresh-session")
        async def refresh_session(request: Request, response: Response):
            """Renova o tempo da sessão"""
            session = session_manager.get_session(request)
            if not session:
                raise HTTPException(status_code=401, detail="Sessão não encontrada")

            # Atualiza o tempo de expiração
            session_id = request.cookies.get("pdv_session")
            session_manager.redis.expire(f"session:{session_id}", 8 * 60 * 60)

            return {"message": "Sessão renovada com sucesso"}

        @self.loginRT.get("/debug-sessions")
        async def debug_sessions():
            """Endpoint para debug - lista todas as sessões no Redis"""
            try:
                keys = session_manager.redis.keys("session:*")
                sessions = {}
                for key in keys:
                    ttl = session_manager.redis.ttl(key)
                    data = session_manager.redis.get(key)
                    sessions[key] = {"ttl_seconds": ttl, "ttl_hours": round(ttl / 3600, 2), "data": json.loads(data) if data else None}
                return {"total_sessions": len(keys), "sessions": sessions}
            except Exception as e:
                return {"error": str(e)}
