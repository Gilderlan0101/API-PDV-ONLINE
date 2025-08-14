from zoneinfo import ZoneInfo
from fastapi import APIRouter, Body, status, Depends, HTTPException
from src.auth.deps import get_current_user
from sqlmodel import Session, select
from datetime import datetime

from src.conf.database import engine
from src.model.user import Usuario
from src.model.sale import Sales
from src.model.product import Produto

router = APIRouter()


@router.post('/cancel', status_code=status.HTTP_200_OK)
async def cancel_sale(
    code: str = Body(..., description="Código da venda a ser cancelada"),
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user.id:
        raise HTTPException(status_code=400, detail='Invalid user')

    with Session(engine) as session:
        try:
            # Busca a venda pelo código
            sale = session.exec(
                select(Sales).where(
                    Sales.codigo_da_venda == code,
                    Sales.funcionario_id == current_user.id,
                )
            ).first()

            if not sale:
                raise HTTPException(status_code=404, detail='Sale not found')

            # Recupera o produto relacionado
            product = session.get(Produto, sale.produto_id)
            if not product:
                raise HTTPException(status_code=404, detail='Product not found')

            # Devolve a quantidade ao estoque
            product.stock += sale.quantity
            product.atualizado_em = datetime.now(ZoneInfo('America/Sao_Paulo'))
            session.add(product)

            # Remove a venda
            session.delete(sale)
            session.commit()

            return {
                "message": "Sale canceled successfully",
                "restored_stock": product.stock,
                "product_id": product.id,
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
