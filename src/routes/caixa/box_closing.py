from fastapi import Depends, HTTPException, status
from src.auth.deps import get_current_user
from src.controllers.caixa.cash_controller import CashController
from src.routes.caixa.operador_caixa import operador
from src.model.user import Usuario
from src.model.caixa import Caixa # Importação do modelo Caixa é necessária aqui

from src.controllers.caixa.cash_controller import CashController

@operador.get('/fechamento/valores')
async def collection_of_the_day(current_user: Usuario = Depends(get_current_user)):
    '''
    Buscando informações sobre os caixas fechados
    '''
    # A sua rota já está filtrando pelo usuario_id do usuário logado.
    var = await CashController.get_caixa_details(current_user.id)
    return var

@operador.post('/fechamento/{caixa_id}') # Rota agora recebe o ID do caixa
async def fechamento_caixa(
    caixa_id: int, # Parâmetro do ID do caixa
    current_user: Usuario = Depends(get_current_user),
):
    """Fecha um caixa da empresa, permitindo o gerenciamento por múltiplos funcionários."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado"
        )

    try:
        # 1. Encontra o caixa
        caixa_a_fechar = await Caixa.get_or_none(id=caixa_id)
        if not caixa_a_fechar:
            raise HTTPException(
                status_code=404,
                detail="Caixa não encontrado."
            )

        # 2. Verifica se o usuário pertence à mesma empresa do caixa
        # Assumindo que o seu modelo Caixa tem uma chave estrangeira para a empresa (usuario_id)
        if caixa_a_fechar.usuario_id != current_user.id:
            # Em um sistema de caixas compartilhados, você verificaria o ID da empresa.
            # Aqui, mantive a verificação pelo usuário que abriu para manter a compatibilidade
            # com a sua lógica de abrir caixa.
            # Se você implementar o modelo de empresa_id na tabela Caixa, a verificação seria:
            # if caixa_a_fechar.empresa_id != current_user.empresa_id:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para fechar este caixa."
            )

        # 3. Fecha o caixa
        resultado = await CashController.fechar_caixa(caixa_id=caixa_id)

        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="O caixa não pôde ser fechado, pois não está aberto."
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