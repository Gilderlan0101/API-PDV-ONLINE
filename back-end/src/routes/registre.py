from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select
from passlib.hash import bcrypt

from ..model.user.users import Usuario
from ..conf.database import engine
from ..schemas.schema_user import CompanyRegisterSchema

# Autenticação
from ..auth.auth_jwt import get_hashed_password

# Matenha a organização do codigo


class RegisterRoute:
    def __init__(self):
        self.registerRT = APIRouter(
            prefix='/auth',  # Prefixo para todas as rotas deste router
            tags=['Autenticação'],  # Nome do grupo no /docs
        )
        self.startup_route()

    def startup_route(self):
        """Define e registra as rotas relacionadas ao registro."""

        @self.registerRT.post('/cadastro', status_code=status.HTTP_201_CREATED)
        async def register(user: CompanyRegisterSchema):
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
                hashed_password = get_hashed_password(user.pwd)

                # Cria o usuário com todos os campos adicionais
                new_user = Usuario(
                    username=user.full_name,
                    email=user.email,
                    password=hashed_password,
                    company_name=user.company_name,
                    trade_name=getattr(user, 'trade_name', None),
                    membros=getattr(user, 'membros', 0),
                    cpf=user.cpf,
                    cnpj=user.cnpj,
                    state_registration=getattr(
                        user, 'state_registration', None
                    ),
                    municipal_registration=getattr(
                        user, 'municipal_registration', None
                    ),
                    cnae_principal=getattr(user, 'cnae_principal', None),
                    crt=getattr(user, 'crt', None),
                    cep=getattr(user, 'cep', None),
                    street=getattr(user, 'street', None),
                    number=getattr(user, 'number', None),
                    complement=getattr(user, 'complement', None),
                    district=getattr(user, 'district', None),
                    city=getattr(user, 'city', None),
                    state=getattr(user, 'state', None),
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
