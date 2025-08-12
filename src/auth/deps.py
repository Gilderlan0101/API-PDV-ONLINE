from datetime import datetime
from typing import Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlmodel import Session, select

from ..auth.auth_jwt import ALGORITHM, JWT_SECRET_KEY
from ..conf.database import engine
from ..model.user.users import Usuario
from ..schemas.schema_user import SystemUser, TokenPayload

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl='/auth/login', scheme_name='JWT'  # URL do endpoint de login
)


async def get_current_user(
    token: str = Depends(reuseable_oauth),
) -> SystemUser:
    """
    Valida o token JWT, verifica o usuário no banco e retorna o usuário do sistema.
    """
    try:
        # Decodifica o token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        # Verifica se o token expirou
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

    # Busca usuário no banco de dados
    with Session(engine) as session:
        sub = token_data.sub

        if not sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Token inválido: identificador de usuário ausente.',
            )

        user_id = int(sub)

        user_db = session.exec(select(Usuario).where(Usuario.id == user_id)).first()

    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Usuário não encontrado no sistema.',
        )

    return SystemUser.model_validate(user_db)
