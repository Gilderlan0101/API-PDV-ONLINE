import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from src.model.user import Usuario
from src.model.caixa import Caixa
from src.auth.deps import get_current_user, SystemUser
from src.controllers.caixa.cash_controller import CashController

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/caixa/{caixa_id}/resumo')
async def resumo_caixa(
    caixa_id: int,
    current_user: SystemUser = Depends(get_current_user),
):
    """Retorna o resumo do caixa antes do fechamento."""

    logger.info("Solicitando resumo do caixa", extra={"caixa_id": caixa_id, "user_id": current_user.id})

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    try:
        caixa = await Caixa.get_or_none(id=caixa_id, usuario_id=current_user.id)
        if not caixa:
            logger.warning("Caixa não encontrado", extra={"caixa_id": caixa_id})
            raise HTTPException(status_code=404, detail="Caixa não encontrado.")

        if not caixa.aberto:
            logger.warning("Tentativa de resumo em caixa fechado", extra={"caixa_id": caixa_id})
            raise HTTPException(status_code=400, detail="Este caixa já está fechado.")

        dados = await CashController.get_caixa_details(caixa_id)

        logger.info("Resumo do caixa gerado com sucesso", extra={"caixa_id": caixa_id})
        saldo_formatado = f'{caixa.saldo_atual:,.2f}'
        return {"status": 200, "dados": dados, "valor_sugerido_fechamento": saldo_formatado}

    except Exception as e:
        logger.error("Erro ao gerar resumo do caixa", extra={"caixa_id": caixa_id, "error": str(e)}, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
