from datetime import datetime
from typing import Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlmodel import Session, select

from ..auth.auth_jwt import ALGORITHM, JWT_SECRET_KEY
from ..conf.database import engine
from ..model.user import Usuario
from ..model.employee import Employees
from ..schemas.schema_user import SystemUser, TokenPayload

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl='/auth/login', scheme_name='JWT'  # URL do endpoint de login
)


async def get_current_user(token: str = Depends(reuseable_oauth)) -> SystemUser:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        token_data = TokenPayload(**payload)

        if (
            token_data.exp is None
            or datetime.fromtimestamp(token_data.exp) < datetime.now()
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Token expirado. Faça login novamente.',
                headers={'WWW-Authenticate': 'Bearer'},
            )

    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Não foi possível validar suas credenciais.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    with Session(engine) as session:
        sub = token_data.sub

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Token inválido: identificador ausente.',
            )

        user_id = int(sub)

        # 🔹 1️⃣ Tenta buscar como Usuario
        user_db = session.exec(select(Usuario).where(Usuario.id == user_id)).first()
        if user_db:
            return SystemUser.model_validate(user_db)

        # 🔹 2️⃣ Se não for Usuario, tenta buscar como Funcionário
        employee_db = session.exec(
            select(Employees).where(Employees.id == user_id)
        ).first()
        if employee_db:
            if not employee_db.ativo:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Funcionário inativo.',
                )
            # Você pode criar outro schema para funcionário ou adaptar SystemUser
            return SystemUser.model_validate(employee_db)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Usuário ou funcionário não encontrado.',
    )
