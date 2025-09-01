import json
from fastapi import APIRouter, HTTPException, status
from tortoise.transactions import in_transaction

from ..auth.auth_jwt import get_hashed_password
from ..model.user import Usuario, CNPJCache
from ..schemas.schema_user import CompanyRegisterSchema
from ..services.consulting_cnpj import consulting_CNPJ

registerRT = APIRouter(
    prefix='/auth',
    tags=['Autenticação']
)


@registerRT.post('/cadastro', status_code=status.HTTP_201_CREATED)
async def register(user: CompanyRegisterSchema):
    # Verifica se o email já existe
    existing_user = await Usuario.filter(email=user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email já cadastrado.')

    # Criptografa a senha
    hashed_password = get_hashed_password(user.pwd)

    # Cria o usuário
    new_user = Usuario(
        username=user.full_name,
        email=user.email,
        password=hashed_password,
        company_name=user.company_name,
        trade_name=getattr(user, 'trade_name', None),
        membros=getattr(user, 'membros', 0),
        cpf=user.cpf,
        cnpj=user.cnpj,
        state_registration=getattr(user, 'state_registration', None),
        municipal_registration=getattr(user, 'municipal_registration', None),
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

    async with in_transaction() as conn:
        await new_user.save(using_db=conn)

        # Busca dados do CNPJ e salva no cache
        if user.cnpj:
            searching_for_data = await consulting_CNPJ(str(user.cnpj))
            full_data = CNPJCache(
                cnpj=user.cnpj,
                data_json=json.dumps(searching_for_data, ensure_ascii=False),
                usuario_id=new_user.id
            )
            await full_data.save(using_db=conn)

    # Retorno seguro (sem senha)
    return {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'empresa': new_user.company_name,
        'criado_em': new_user.criado_em.strftime('%d/%m/%Y %H:%M:%S')
    }
