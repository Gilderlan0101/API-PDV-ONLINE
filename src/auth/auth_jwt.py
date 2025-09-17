import os
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

load_dotenv()

# Chamando as variaves de ambiete que vmos usar neste arquivo
ALGORITHM = os.getenv('ALGORITHM')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_REFRESH_SECRET_KEY = os.getenv('JWT_REFRESH_SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[int] = None) -> str:
    expire = (
        datetime.now(ZoneInfo('America/Sao_Paulo')) + timedelta(minutes=expires_delta)
        if expires_delta
        else datetime.now(ZoneInfo('America/Sao_Paulo')) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {'exp': expire, 'sub': str(subject)}
    return jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)  # type: ignore


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[int] = None) -> str:
    expire = (
        datetime.now(ZoneInfo('America/Sao_Paulo')) + timedelta(minutes=expires_delta)
        if expires_delta
        else datetime.now(ZoneInfo('America/Sao_Paulo')) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )

    to_encode = {'exp': expire, 'sub': str(subject)}
    # type: ignore
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
