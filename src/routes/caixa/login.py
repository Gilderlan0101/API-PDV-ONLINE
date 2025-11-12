from fastapi import APIRouter, HTTPException, status, Body, Request, Response, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from src.schemas.login.form_login_checkout import CustomOAuth2PasswordRequestForm
from src.controllers.caixa.cash_controller import CashController
from src.auth.deps_employes import SystemEmployees
from src.model.user import Usuario
from src.model.employee import Employees
from src.model.caixa import Caixa
from src.auth.auth_jwt import create_access_token, create_refresh_token, verify_password, verify_token
from src.logs.infos import LOGGER


# -------------------------------------------------------------
# 🔥 SCHEMAS
# -------------------------------------------------------------
class TokenCaixaSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    empresa: Optional[str] = None
    empresa_id: Optional[int] = None
    tipo: str
    message: str
    access_token: str
    refresh_token: str
    token_type: str
    value: float
    caixa_id: int
    caixa_status: str  # ✅ NOVO: status do caixa (aberto/fechado)


class ValidateTokenResponse(BaseModel):
    valid: bool
    user_id: int
    username: str
    empresa: str
    empresa_id: int
    caixa_aberto: bool
    caixa_id: Optional[int]
    saldo_inicial: Optional[float]
    message: str


# -------------------------------------------------------------
# CLASSE PRINCIPAL REFATORADA
# -------------------------------------------------------------
class LoginCheckout:
    def __init__(self):
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        @self.router.post(
            "/open",
            status_code=status.HTTP_200_OK,
            response_model=TokenCaixaSchema,
        )
        async def login(user: CustomOAuth2PasswordRequestForm = Depends()):
            """
            Login para funcionários com verificação e abertura de caixa
            """
            LOGGER.info(f"🔐 Tentativa de login: {user.username}")

            # Verifica se é admin
            is_admin = await Usuario.get_or_none(email=user.username)
            if is_admin:
                raise HTTPException(status_code=403, detail="Administradores não podem abrir um caixa.")

            # Verifica funcionário
            employee = await Employees.get_or_none(email=user.username).select_related("usuario")
            if not employee:
                raise HTTPException(status_code=401, detail="Credenciais inválidas")

            # Verifica a senha
            if not verify_password(user.password, employee.senha):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")

            if not employee.ativo:
                raise HTTPException(status_code=403, detail="Funcionário inativo.")

            if not employee.usuario:
                raise HTTPException(status_code=403, detail="Funcionário não vinculado a uma empresa.")

            # --- VERIFICAÇÃO DE CAIXA EXISTENTE ---
            caixa_aberto = await Caixa.filter(
                funcionario_id=employee.id, 
                usuario_id=employee.usuario_id,
                aberto=True
            ).first()

            caixa_status = "reaberto"
            caixa = None

            if caixa_aberto:
                # Caixa já está aberto - apenas retorna os dados
                LOGGER.info(f"ℹ️  Caixa já aberto para {employee.nome} - ID: {caixa_aberto.caixa_id}")
                caixa = caixa_aberto
                caixa_status = "ja_aberto"
            else:
                try:
                    # Abre um novo caixa
                    caixa = await CashController.abrir_caixa(
                        funcionario_id=employee.id,
                        saldo_inicial=float(user.valor_inicial),
                        nome=f"Caixa - {employee.nome}",
                        company_id=employee.usuario_id,
                    )
                    caixa_status = "novo"
                    LOGGER.info(f"✅ Novo caixa aberto para {employee.nome}: ID {caixa.caixa_id}")
                except Exception as e:
                    LOGGER.error(f"❌ Erro ao abrir caixa para {employee.id}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        detail=f"Erro ao tentar abrir o caixa: {str(e)}"
                    )

            # Gera os tokens JWT
            access_token = create_access_token(str(employee.id))
            refresh_token = create_refresh_token(str(employee.id))

            # Mensagem baseada no status do caixa
            if caixa_status == "ja_aberto":
                message = "Login realizado - Caixa já estava aberto"
            elif caixa_status == "reaberto":
                message = "Login realizado - Caixa reaberto"
            else:
                message = "Login e Caixa abertos com sucesso"

            return {
                "id": employee.id,
                "username": employee.nome,
                "email": employee.email,
                "value": float(user.valor_inicial),
                "empresa": employee.usuario.company_name,
                "empresa_id": employee.usuario_id,
                "tipo": "funcionario",
                "message": message,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "caixa_id": caixa.caixa_id,
                "caixa_status": caixa_status,  # ✅ Status do caixa
            }

        @self.router.post("/logout")
        async def logout(request: Request, response: Response):
            """
            Faz logout e fecha o caixa do funcionário
            """
            auth_header = request.headers.get("Authorization")
            revoked_token = None

            if auth_header and auth_header.startswith("Bearer "):
                revoked_token = auth_header.replace("Bearer ", "")
                employee_id = None

                try:
                    # 1. Obtém o employee_id do token
                    employee_id = verify_token(revoked_token)

                    if employee_id:
                        # 2. ✅ FECHA O CAIXA DO FUNCIONÁRIO
                        caixa_fechado = await CashController.fechar_caixa(funcionario_id=int(employee_id))
                        
                        if caixa_fechado:
                            LOGGER.info(f"✅ Caixa fechado para Funcionário ID: {employee_id} - Caixa ID: {caixa_fechado.caixa_id}")
                        else:
                            LOGGER.info(f"ℹ️  Nenhum caixa aberto encontrado para Funcionário ID: {employee_id}")

                except HTTPException:
                    # Token inválido, mas ainda fazemos o logout
                    pass
                except Exception as e:
                    LOGGER.error(f"⚠️ Erro ao fechar caixa para token {revoked_token[:10]}...: {e}")

                # 3. Adiciona o token a um blocklist (placeholder)
                LOGGER.info(f"Token JWT revogado: {revoked_token[:10]}...")

            else:
                LOGGER.warning("Tentativa de logout sem token Bearer no header.")

            return {
                "message": "Logout realizado com sucesso", 
                "caixa_fechado": employee_id is not None
            }

        @self.router.get("/validate", response_model=ValidateTokenResponse)
        async def validate_token(request: Request):
            """
            Valida se o token JWT é válido e se o caixa está aberto
            """
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token não fornecido")

            token = auth_header.replace("Bearer ", "")

            try:
                # 🚨 AQUI: Verificar se o token está na blocklist

                # Verifica se o token JWT é válido
                employee_id = verify_token(token)

                if not employee_id:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

                # Busca o funcionário
                employee = await Employees.get_or_none(id=int(employee_id)).select_related("usuario")
                if not employee:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

                # Verifica se o funcionário está ativo
                if not employee.ativo:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário inativo")

                # ✅ VERIFICA SE O CAIXA ESTÁ ABERTO (CORRIGIDO)
                caixa_aberto = await Caixa.filter(
                    funcionario_id=employee.id, 
                    usuario_id=employee.usuario_id,
                    aberto=True
                ).order_by('-id').first()

                if not caixa_aberto:
                    return {
                        "valid": True,
                        "user_id": employee.id,
                        "username": employee.nome,
                        "empresa": employee.usuario.company_name if employee.usuario else "N/A",
                        "empresa_id": employee.usuario_id,
                        "caixa_aberto": False,
                        "caixa_id": None,
                        "saldo_inicial": None,
                        "message": "Token válido, mas caixa não está aberto",
                    }

                # ✅ Tudo validado com sucesso - caixa aberto
                return {
                    "valid": True,
                    "user_id": employee.id,
                    "username": employee.nome,
                    "empresa": employee.usuario.company_name if employee.usuario else "N/A",
                    "empresa_id": employee.usuario_id,
                    "caixa_aberto": True,
                    "caixa_id": caixa_aberto,
                    "saldo_inicial": float(caixa_aberto.saldo_inicial),
                    "message": "Token e sessão válidos - Caixa aberto",
                }

            except HTTPException:
                raise
            except Exception as e:
                LOGGER.error(f"Erro na validação do token: {str(e)}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

        # 🔥 NOVA ROTA: Status do caixa
        @self.router.get("/caixa/status")
        async def get_caixa_status(current_user: SystemEmployees = Depends()):
            """
            Retorna o status atual do caixa do funcionário
            """
            try:
                caixa_aberto = await Caixa.filter(
                    funcionario_id=current_user.id, 
                    usuario_id=current_user.usuario_id,
                    aberto=True
                ).first()

                if caixa_aberto:
                    return {
                        "caixa_aberto": True,
                        "caixa_id": caixa_aberto.caixa_id,
                        "saldo_inicial": caixa_aberto.saldo_inicial,
                        "saldo_atual": caixa_aberto.saldo_atual,
                        "aberto_em": caixa_aberto.criado_em,
                        "message": "Caixa está aberto"
                    }
                else:
                    return {
                        "caixa_aberto": False,
                        "message": "Nenhum caixa aberto encontrado"
                    }

            except Exception as e:
                LOGGER.error(f"Erro ao verificar status do caixa: {e}")
                raise HTTPException(status_code=500, detail="Erro ao verificar status do caixa")