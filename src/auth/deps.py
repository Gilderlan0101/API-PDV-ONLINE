from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, ValidationError

from src.auth.auth_jwt import ALGORITHM, JWT_SECRET_KEY
from src.model.user import Usuario
from src.model.employee import Employees
from src.model.user import Membro
from src.schemas.schema_user import TokenPayload

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="JWT")


async def get_current_user(token: str = Depends(reuseable_oauth)) -> "SystemUser":
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        if token_data.exp is None or datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado. Faça login novamente.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não foi possível validar suas credenciais.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = token_data.sub
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido: identificador ausente.",
        )

    user_id = int(sub)

    # 🔹 1) Tenta buscar como Usuario (dono da empresa)
    user_db = await Usuario.get_or_none(id=user_id)
    if user_db:
        return SystemUser.model_validate(user_db).model_copy(update={"empresa_id": user_db.id})

    # 🔹 2) Tenta buscar como Funcionário
    employee_db = await Employees.get_or_none(id=user_id).select_related("usuario")
    if employee_db:
        if not employee_db.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Funcionário inativo.",
            )

        usuario = employee_db.usuario
        return SystemUser(
            id=employee_db.id,
            username=usuario.username if usuario else employee_db.nome,
            email=employee_db.email or (usuario.email if usuario else "sem_email@empresa.com"),
            company_name=usuario.company_name if usuario else "Empresa não definida",
            cnpj=usuario.cnpj if usuario else None,
            cpf=None,
            is_active=employee_db.ativo,
            empresa_id=usuario.id if usuario else None,  # 🔹 aqui
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuário ou funcionário não encontrado.",
    )

    # Tentando com Membors
    membro_db = Membro.get_or_none(id=user_id).select_related("usuario")
    if membro_db:
        if not membro_db.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado..",
                )


        membro = membro_db.usuario

        return SystemUser(
            id=membro.id,
            username=membro.nome if usuario else membro.nome,
            email=membro.email or (usuario.email if usuario else None),
            gerente=membro.gerente or None,
            cnpj=membro.cnpj if usuario.cnpj else None,
            cpf=membro.cpf,
            is_active=membro.ativo,
            empresa_id=usuario.id if usuario else None,  # 🔹 aqui
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuário ou funcionário não encontrado.",
    )



from typing import Optional
from pydantic import BaseModel, EmailStr

class SystemUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    company_name: Optional[str] = None
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    gerente: Optional[str] = None  # ✅ Correto - use ":" em vez de "="
    is_active: bool = True
    empresa_id: Optional[int] = None

    model_config = {'from_attributes': True}