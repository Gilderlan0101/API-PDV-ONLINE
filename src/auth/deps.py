# deps.py - Versão Corrigida

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, ValidationError

from src.auth.auth_jwt import ALGORITHM, JWT_SECRET_KEY
from src.model.user import Usuario
from src.model.employee import Employees
from src.model.membros import Membro
from src.schemas.schema_user import TokenPayload

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="JWT")


class SystemUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    company_name: Optional[str] = None
    cnpj: Optional[str] = None
    cpf: Optional[str] = None
    gerente: Optional[str] = None
    is_active: bool = True
    empresa_id: Optional[int] = None  # ID da empresa MASTER (não do usuário)

    model_config = {'from_attributes': True}


async def get_current_user(token: str = Depends(reuseable_oauth)) -> SystemUser:
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

    print(f"🔍 Buscando usuário com ID: {user_id}")

    # 🔹 1) Tenta buscar como Usuario (dono da empresa)
    user_db = await Usuario.get_or_none(id=user_id)
    if user_db:
        print(f"✅ Usuário encontrado: {user_db.username}")
        print(f"🏢 ID da Empresa (usuário é dono): {user_db.id}")

        # Usuário é dono da empresa -> empresa_id = seu próprio ID
        return SystemUser(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            company_name=user_db.company_name,
            cnpj=user_db.cnpj,
            cpf=user_db.cpf,
            is_active=user_db.is_active,
            empresa_id=user_db.id,  # Usuário é a empresa master
        )

    # Tenta buscar como Membro
    membro_db = await Membro.get_or_none(id=user_id).select_related("usuario")
    if membro_db:
        print(f"✅ Membro encontrado: {membro_db.nome}")

        if not membro_db.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Membro inativo.",
            )

        # Busca o usuário DONO da empresa
        usuario_dono = membro_db.usuario
        if not usuario_dono:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Membro não vinculado a uma empresa principal.",
            )

        print(f"👤 Membro: {membro_db.nome} (ID: {membro_db.id})")
        print(f"🏢 Pertence à empresa: {usuario_dono.company_name} (ID: {usuario_dono.id})")

        return SystemUser(
            id=membro_db.id,  # ID do membro
            username=membro_db.nome,
            email=membro_db.email or usuario_dono.email,
            company_name=usuario_dono.company_name,
            cnpj=usuario_dono.cnpj,
            cpf=membro_db.cpf,
            gerente=membro_db.gerente,
            is_active=membro_db.ativo,
            empresa_id=usuario_dono.id,  # 🎯 ID da EMPRESA MASTER (não do membro)
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuário, funcionário ou membro não encontrado.",
    )
