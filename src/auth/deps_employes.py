import logging
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, ValidationError
from datetime import datetime
from typing import Final

from src.model.employee import Employees
from src.model.caixa import Caixa
from src.schemas.schema_user import TokenPayload
from src.auth.auth_jwt import verify_password  # ← IMPORTANTE: Adicionar esta importação
from src.logs.infos import LOGGER

from src.auth.auth_jwt import ALGORITHM, JWT_SECRET_KEY

# -------------------------------------------------------------
# 1. Schemas de Retorno
# -------------------------------------------------------------


class SystemEmployees(BaseModel):
    id: int
    username: str
    company_name: str
    email: EmailStr
    empresa_id: int
    checkout_id: int

    model_config = {"from_attributes": True}


# -------------------------------------------------------------
# 2. Configuração do OAuth2
# -------------------------------------------------------------

reuseable_oauth: Final = OAuth2PasswordBearer(tokenUrl="/checkout/open", scheme_name="JWT", auto_error=False)  # ← CORRIGIDO: adicionar barra

# -------------------------------------------------------------
# 3. Função de Verificação de Senha (NOVA)
# -------------------------------------------------------------


async def authenticate_employee(email: str, password: str) -> Employees:
    """
    Autentica um funcionário por email e senha.

    Args:
        email: Email do funcionário
        password: Senha em texto puro

    Returns:
        Employees: Objeto do funcionário se autenticado

    Raises:
        HTTPException: 401 para credenciais inválidas
    """
    LOGGER.info(f"🔐 Tentativa de autenticação para: {email}")

    # Busca funcionário com relacionamento de usuário
    employee = await Employees.get_or_none(email=email).select_related("usuario")

    if not employee:
        LOGGER.warning(f"❌ Email não encontrado: {email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    # Verifica senha
    if not verify_password(password, employee.senha):
        LOGGER.warning(f"❌ Senha incorreta para: {email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    # Verifica se funcionário está ativo
    if not employee.ativo:
        LOGGER.warning(f"❌ Funcionário inativo: {email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário inativo")

    # Verifica se tem empresa vinculada
    if not employee.usuario:
        LOGGER.warning(f"❌ Funcionário sem empresa: {email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário não vinculado a uma empresa")

    LOGGER.info(f"✅ Autenticação bem-sucedida para: {email}")
    return employee


# -------------------------------------------------------------
# 4. Função de Dependência Principal (CORRIGIDA)
# -------------------------------------------------------------


async def get_current_employee(token: str = Depends(reuseable_oauth)) -> SystemEmployees:
    """
    Decodifica o token JWT e retorna os dados do funcionário.
    NÃO abre caixa automaticamente - isso deve ser feito apenas na rota /open.
    """

    # --- 3.1. Validação do Token JWT ---
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        # Verifica expiração
        if token_data.exp is None or datetime.fromtimestamp(token_data.exp) < datetime.now():
            LOGGER.info("❌ Token expirado na validação de dependência.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Faça login novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except (JWTError, ValidationError) as erro:
        LOGGER.error(f"❌ Falha na decodificação/validação do token: {erro}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Não foi possível validar suas credenciais.", headers={"WWW-Authenticate": "Bearer"}
        )

    employee_id = int(token_data.sub)
    if not employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido: identificador (sub) ausente.")

    # --- 3.2. Busca do Funcionário ---
    employee = await Employees.get_or_none(id=int(employee_id)).select_related("usuario")

    if not employee or not employee.usuario:
        LOGGER.warning(f"❌ Tentativa de acesso com ID {employee_id} falhou: Funcionário ou Admin não encontrados.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Funcionário ou empresa principal não encontrados.")

    if not employee.ativo:
        LOGGER.warning(f"❌ Funcionário {employee.id} tentou acessar mas está inativo.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário inativo.")

    admin = employee.usuario
    LOGGER.info(f"✅ Funcionario {employee.id} da EMPRESA {admin.company_name} validado via JWT.")

    # --- 3.3. Busca do CAIXA ABERTO (APENAS VERIFICAÇÃO) ---
    caixa_aberto = await Caixa.filter(funcionario_id=employee.id, usuario_id=admin.id, aberto=True).order_by('-id').first()

    checkout_id = caixa_aberto.id if caixa_aberto else None

    if not checkout_id:
        LOGGER.warning(f"⚠️  Funcionário {employee.id} autenticado mas sem caixa aberto")

    # --- 3.4. Retorno dos Dados ---
    return SystemEmployees(
        id=employee.id,
        username=employee.nome,
        company_name=admin.company_name,
        email=employee.email,
        empresa_id=admin.id,
        checkout_id=checkout_id,  # Pode ser None se não houver caixa aberto
    )
