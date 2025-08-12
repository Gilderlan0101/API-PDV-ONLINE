import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import Session, select

from ..conf.database import engine
from ..model.user.users import CNPJCache, Usuario
from ..services.consulting_cnpj import consulting_CNPJ


class ConsultaRoute:
    def __init__(self):
        self.router = APIRouter(prefix='/consulta', tags=['Consulta CNPJ / Usuário'])
        self.startup_route()

    def startup_route(self):
        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def consulta_dados(
            email: Optional[str] = Query(default=None),
            cnpj: Optional[str] = Query(default=None),
        ):
            if not email and not cnpj:
                raise HTTPException(
                    status_code=400,
                    detail='Você deve fornecer email ou cnpj para consulta.',
                )

            with Session(engine) as session:
                # Busca por email ou cnpj no Usuario
                query = select(Usuario)
                if email:
                    query = query.where(Usuario.email == email)
                elif cnpj:
                    query = query.where(Usuario.cnpj == cnpj)

                user = session.exec(query).first()

                if user:
                    # Se achar no banco retorna dados já salvos
                    return {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'company_name': user.company_name,
                        'trade_name': user.trade_name,
                        'cpf': user.cpf,
                        'cnpj': user.cnpj,
                        'state_registration': user.state_registration,
                        'municipal_registration': user.municipal_registration,
                        'cnae_principal': user.cnae_principal,
                        'crt': user.crt,
                        'cep': user.cep,
                        'street': user.street,
                        'number': user.number,
                        'complement': user.complement,
                        'district': user.district,
                        'city': user.city,
                        'state': user.state,
                    }

                # Se não encontrar usuário, tenta buscar na API via CNPJ (se informado)
                if cnpj:
                    # Verifica se cache existe e está válido
                    cache = session.exec(
                        select(CNPJCache).where(CNPJCache.cnpj == cnpj)
                    ).first()

                    if cache and cache.is_valid():
                        data = json.loads(cache.data_json)
                    else:
                        data = await consulting_CNPJ(cnpj)
                        # Salva ou atualiza cache
                        if cache:
                            cache.data_json = json.dumps(data, ensure_ascii=False)
                            cache.updated_at = datetime.now()
                        else:
                            # Aqui, se não tem usuário, não tem usuario_id para vincular.
                            # Pode ser None ou omitir se quiser
                            cache = CNPJCache(
                                cnpj=cnpj,
                                data_json=json.dumps(data, ensure_ascii=False),
                                usuario_id=None,
                            )
                            session.add(cache)
                        session.commit()

                    return data

                # Se não passou cnpj e não achou email, erro
                raise HTTPException(
                    status_code=404,
                    detail='Nenhum dado encontrado para os parâmetros fornecidos.',
                )
