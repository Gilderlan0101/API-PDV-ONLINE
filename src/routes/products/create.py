from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional

from src.auth.deps import get_current_user
from src.conf.database import engine
from src.model.product import Produto
from src.model.user import Usuario
from src.schemas.schema_product import ProductRegisterSchema

router = APIRouter()

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_product(
    prod: ProductRegisterSchema,
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user.id:
        raise HTTPException(status_code=400, detail='Usuário inválido')

    with Session(engine) as session:
        try:
            date_expired = (
                datetime.combine(prod.date_expired, datetime.min.time())
                if prod.date_expired
                else None
            )
            image_url = str(prod.image_url) if prod.image_url else None

            register_prod = Produto(
                product_code=prod.product_code,
                name=prod.name,
                stock=prod.stock,
                stoke_min=prod.stoke_min,
                stoke_max=prod.stoke_max,
                date_expired=date_expired,
                fabricator=prod.fabricator,
                cost_price=prod.cost_price,
                price_uni=prod.price_uni,
                sale_price=prod.sale_price,
                supplier=prod.supplier,
                lot_bar_code=prod.lot_bar_code,
                image_url=image_url,
                usuario_id=current_user.id,
                product_type=prod.product_type,
                active=prod.active,
                group=prod.group,
                sector=prod.sector,
                unit=prod.unit,
                controllstoke=prod.controllstoke,
                sales_config=prod.sales_config.json() if prod.sales_config else None,
            )

            session.add(register_prod)
            session.commit()
            session.refresh(register_prod)

            return {
                'message': 'Produto cadastrado com sucesso!',
                'product_id': register_prod.id,
                'usuario_id': current_user.id,
            }
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=f'Erro: {e}')
