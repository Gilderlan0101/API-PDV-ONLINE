from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from src.auth.deps import get_current_user
from src.conf.database import engine
from src.model.product import Produto, ProdutoArquivado
from src.model.user import Usuario
from src.routes.products.helpers import get_product_by_user, to_dict

router = APIRouter()


@router.delete('/remove', status_code=status.HTTP_200_OK)
async def delete_product(
    code: str = Query(..., description='Código do produto'),
    description: str = Query(..., description='Motivo do arquivamento'),
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user.id:
        raise HTTPException(status_code=400, detail='Usuário inválido')

    with Session(engine) as session:
        product = get_product_by_user(session, current_user.id, code)
        if not product:
            raise HTTPException(
                status_code=404,
                detail='Produto não encontrado ou não pertence ao usuário',
            )

        product_data = to_dict(product)
        product_data['description'] = description
        product_data.pop('id', None)
        product_data.pop('criado_em', None)
        product_data.pop('atualizado_em', None)

        archived_product = ProdutoArquivado(**product_data)
        session.add(archived_product)
        session.delete(product)
        session.commit()

    return {
        'message': f"Produto '{product.name}' removido e arquivado com sucesso!",
        'usuario_id': current_user.id,
    }
