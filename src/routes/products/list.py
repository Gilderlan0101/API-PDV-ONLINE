from typing import Optional
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from pydantic import ValidationError

from src.auth.deps import get_current_user
from src.conf.database import engine
from src.model.product import Produto
from src.model.user import Usuario
from src.schemas.avisos import RelatorioOut, ResponseOut
from src.controllers.stoke.stoke_control import gerar_relatorio_completo

router = APIRouter()


@router.get('/produtos', response_model=ResponseOut)
async def list_products(current_user: Usuario = Depends(get_current_user)):
    try:
        if not current_user.id:
            raise HTTPException(status_code=400, detail='Usuário inválido')

        with Session(engine) as session:
            produtos_orm = session.exec(
                select(Produto).where(Produto.usuario_id == current_user.id)
            ).all()

        products = []
        for p in produtos_orm:
            products.append(
                {
                    "product_code": p.product_code,
                    "id": p.id,
                    "name": p.name,
                    "sale_price": p.sale_price,
                    "stock_atual": p.stock,
                    "stock_min": p.stoke_min,
                    "stock_max": p.stoke_max,
                  
                    "date_expired": (
                        p.date_expired.isoformat() if p.date_expired else None
                    ),
                    "price_uni": p.price_uni,
		   "lot_bar_code":p.lot_bar_code,
                }
            )

        relatorios_dict = gerar_relatorio_completo(current_user.id)

        try:
            relatorios_obj = RelatorioOut.model_validate(relatorios_dict)
        except ValidationError as e:
            print('Erro na validação do relatório:', e)
            raise HTTPException(status_code=500, detail='Erro no formato do relatório')

        return {
            'products': products,
            'aviso': relatorios_obj,
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
