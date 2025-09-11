from fastapi import Depends, HTTPException
from src.auth.deps import get_current_user
from src.controllers.caixa.cash_controller import CashController
from src.routes.caixa.operador_caixa import operador
from src.model.user import Usuario
#from src.model.caixa import Caixa


from src.controllers.caixa.cash_controller import CashController

@operador.get('/fechamento/valores')
async def collection_of_the_day(current_user: Usuario = Depends(get_current_user)):
    
    '''
    Buscando informaçoes sobre os caixas fechados
    '''

    var = await CashController.get_caixa_details(current_user.id)

    return var



@operador.get('/fechamento')
async def fechamento_caixa(
    current_user: Usuario = Depends(get_current_user),
):
    """Fecha automaticamente o caixa aberto do usuário logado."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Usuário não autenticado"
        )

    try:
        resultado = await CashController.fechar_caixa(usuario_id=current_user.id)

        if not resultado:
            raise HTTPException(
                status_code=404, 
                detail="Nenhum caixa aberto encontrado para este usuário."
            )

        return {
            "status": 200,
            "msg": "Caixa fechado com sucesso.",
            "caixa": resultado[0]["caixa_id"],
            "nome": resultado[0]['nome'],
            "detalhes": resultado[0]["descricao"],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
