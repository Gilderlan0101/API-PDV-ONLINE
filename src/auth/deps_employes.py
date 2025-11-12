import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr, ValidationError
from datetime import datetime
from typing import Final

from src.model.employee import Employees
from src.model.caixa import Caixa
from src.schemas.schema_user import TokenPayload
from src.auth.auth_jwt import JWT_SECRET_KEY, ALGORITHM  # Assumindo que você tem essas constantes
from src.controllers.caixa.cash_controller import CashController  # <--- NECESSÁRIO para abrir o caixa

# LOGS
from src.logs.infos import LOGGER

# -------------------------------------------------------------
# 1. Schemas de Retorno (Mantidos do seu código)
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

reuseable_oauth: Final = OAuth2PasswordBearer(tokenUrl="checkout/open", scheme_name="JWT")

# -------------------------------------------------------------
# 3. Função de Dependência Principal (get_current_employee)
# -------------------------------------------------------------


async def get_current_employee(token: str = Depends(reuseable_oauth)) -> SystemEmployees:
    """
    Decodifica o token JWT, verifica a validade e retorna os dados completos do funcionário/empresa,
    garantindo que um caixa esteja aberto (e abrindo um novo se não estiver).
    """

    # --- 3.1. Validação do Token JWT ---
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        # Verifica expiração
        if token_data.exp is None or datetime.fromtimestamp(token_data.exp) < datetime.now():
            LOGGER.info("Token expirado na validação de dependência.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Faça login novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except (JWTError, ValidationError) as erro:
        LOGGER.error(f"Falha na decodificação/validação do token: {erro}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Não foi possível validar suas credenciais.", headers={"WWW-Authenticate": "Bearer"}
        )

    employee_id = token_data.sub
    if not employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido: identificador (sub) ausente.")

    # --- 3.2. Busca do Funcionário e Admin ---
    employee = await Employees.get_or_none(id=int(employee_id)).select_related("usuario")

    if not employee or not employee.usuario:
        LOGGER.warning(f"Tentativa de login com ID {employee_id} falhou: Funcionário ou Admin não encontrados.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Funcionário ou empresa principal não encontrados.")

    if not employee.ativo:
        LOGGER.warning(f"Funcionário {employee.id} tentou logar mas está inativo.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Funcionário inativo.")

    admin = employee.usuario
    LOGGER.info(f"Funcionario {employee.id} da EMPRESA {admin.company_name} logado via JWT.")

    # --- 3.3. Busca e Abertura do Caixa (Utilizando CashController) ---

    # 💡 Ação: Usamos a classe CashController para garantir a não repetição de código
    # e centralizar a lógica de busca/criação/validação do caixa.

    try:
        # A função CashController.abrir_caixa verifica se já existe um aberto
        # e retorna o caixa existente ou um novo criado.
        caixa_aberto = await CashController.abrir_caixa(
            funcionario_id=employee.id,
            saldo_inicial=0.0,  # Passamos 0.0 pois o valor de abertura real é definido no /login/open
            nome=employee.nome,
            company_id=admin.id,
        )

        # Se o CashController retornar um objeto Caixa, pegamos o ID.
        checkout_id = caixa_aberto.id
        LOGGER.debug(f"Caixa (ID: {checkout_id}) encontrado/aberto com sucesso para o funcionário {employee.id}. [OK]")

    except Exception as e:
        # Captura qualquer falha dentro do CashController (ex: erro de DB)
        LOGGER.error(f"❌ Falha CRÍTICA ao garantir a abertura do caixa: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno ao inicializar o caixa do funcionário.")

    # --- 3.4. Retorno dos Dados ---
    return SystemEmployees(
        id=employee.id,
        username=employee.nome,
        company_name=admin.company_name,
        email=employee.email,
        empresa_id=admin.id,
        checkout_id=checkout_id,  # ID do caixa ativo
    )
