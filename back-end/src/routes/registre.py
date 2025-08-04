from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select
from passlib.hash import bcrypt

from ..model.user.users import Usuario
from ..conf.database import engine
from ..schemas.schema_user import RegistreSchema


# Matenha a organização do codigo


class RegisterRoute:
    def __init__(self):
        self.registerRT = APIRouter(
            prefix="/auth",  # Prefixo para todas as rotas deste router
            tags=["Autenticação"]  # Nome do grupo no /docs
        )
        self.startup_route()

    def startup_route(self):
        """Define e registra as rotas relacionadas ao registro."""

        @self.registerRT.post('/cadastro', status_code=status.HTTP_201_CREATED)
        async def register(user: RegistreSchema):
            """
            Rota para registrar um novo usuário no sistema.
            """
            with Session(engine) as session:
                # Verifica se o email já existe
                if session.exec(
                    select(Usuario).where(Usuario.email == user.email)
                ).first():
                    raise HTTPException(
                        status_code=400, detail='Email já cadastrado.'
                    )

                # Criptografa a senha
                hashed_password = bcrypt.hash(user.pwd)

                # Cria o usuário
                new_user = Usuario(
                    username=user.full_name,
                    email=user.email,
                    password=hashed_password,
                    company_name=user.company_name,
                    cpf=user.cpf,
                    cnpj=user.cnpj,
                    membros=0,
                )

                # Aplica mais uma verificação de entrada de dados

                session.add(new_user)
                session.commit()
                session.refresh(new_user)

                # Retorna dados sem expor senha | Remove em produção
                return {
                    'id': new_user.id,
                    'username': new_user.username,
                    'email': new_user.email,
                    'empresa': new_user.company_name,
                    'criado_em': new_user.criado_em.strftime(
                        '%d/%m/%Y %H:%M:%S'
                    ),
                }
