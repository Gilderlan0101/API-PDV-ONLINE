import logging
from fastapi import APIRouter, Depends
from src.model.user import Usuario
from src.model.caixa import Caixa
from src.auth.deps import get_current_user, SystemUser


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/infos/caixas')
async def information_from_all_cashiers(current_user: SystemUser = Depends(get_current_user)):
    """Retorna informações de todos os caixas do usuário"""

    logger.debug("Listando caixas do usuário", extra={"user_id": current_user.id})

    if not current_user.id:
        raise HTTPException(status_code=404, detail='Usuario não encontrado.')

    user = await Usuario.filter(id=current_user.id).first()
    cashs = await Caixa.filter(usuario_id=user.id).all()

    infos = []
    for data in cashs:
        if data.aberto:
            saldo_formatado = f'{data.saldo_atual:,.2f}'
            infos.append({'Nome': data.nome, 'ID': data.id, 'Aberto': data.aberto, 'Saldo_atual': saldo_formatado})

    logger.debug("Caixas listados", extra={"total_caixas": len(cashs), "caixas_abertos": len(infos)})

    return infos
