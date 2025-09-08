from fastapi import Depends
from src.controllers.caixa.dados_caixa import get_caixa_details
from src.auth.deps import get_current_user
from src.routes.caixa.operador_caixa import operador
from src.model.user import Usuario


@operador.get('fechamento/valore')
async def collection_of_the_day(current_user: Usuario = Depends(get_current_user)):

    var = await get_caixa_details(1, 1)

    return var
