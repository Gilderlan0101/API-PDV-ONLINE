from fastapi import APIRouter, Body, status, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import datetime
from zoneinfo import ZoneInfo

from src.auth.deps import get_current_user
from src.conf.database import engine
from src.model.user import Usuario
from src.model.sale import Sales
from src.model.product import Produto

router = APIRouter()

class CancelRequest(BaseModel):
    code: str
    reason: str | None = None

@router.post('/cancel', status_code=status.HTTP_200_OK)
async def cancel_sale(
    body: CancelRequest,
    current_user: Usuario = Depends(get_current_user),
):
    """Cancela uma venda, restaura estoque e retorna resultado padronizado para frontend"""
    if not current_user.id:
        return {
            "success": False,
            "data": None,
            "error": "Usuário inválido"
        }

    try:
        with Session(engine) as session:
            # Busca a venda pelo código
            sale = session.exec(
                select(Sales).where(
                    Sales.codigo_da_venda == body.code,
                    Sales.funcionario_id == current_user.id
                )
            ).first()

            if not sale:
                return {
                    "success": False,
                    "data": None,
                    "error": "Venda não encontrada"
                }

            # Recupera o produto relacionado
            product = session.get(Produto, sale.produto_id)
            if not product:
                return {
                    "success": False,
                    "data": None,
                    "error": "Produto não encontrado"
                }

            # Restaura o estoque
            product.stock += sale.quantity
            product.atualizado_em = datetime.now(ZoneInfo('America/Sao_Paulo'))
            session.add(product)

            # Remove a venda
            session.delete(sale)
            session.commit()

            return {
                "success": True,
                "data": {
                    "message": "Venda cancelada com sucesso",
                    "restored_stock": product.stock,
                    "product_id": product.id
                },
                "error": None
            }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Erro inesperado: {str(e)}"
        }
