# src/routes/caixa_routes.py (ou onde estão suas rotas atuais)
from fastapi import APIRouter, Depends, HTTPException, status, Body
from src.auth.deps import get_current_user
from src.schemas.funcs.operador_cadastro import (
    CaixaFuncionarioCreate,
    CaixaFuncionarioUpdate,
)
from src.model.user import Usuario
from src.model.caixa import Caixa

from src.controllers.caixa.cash_controller import CashController

operador = APIRouter(prefix='/auth', tags=['Autenticação'])


@operador.post('/abertura')
async def abertura_caixa(
    form: CaixaFuncionarioCreate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """Abre o caixa para um funcionário."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    try:
        caixa = await CashController.abrir_caixa(
            usuario_id=current_user.id,
            funcionario_id=form.funcionario_id,
            saldo_inicial=form.valor_abertura,
            nome=f"Caixa {form.funcionario_id} - {current_user.company_name}",
        )

        return {"status": 200, "msg": "Caixa aberto com sucesso.", "caixa": caixa}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@operador.post('/fechamento')
async def fechamento_caixa(
    form: CaixaFuncionarioUpdate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """Fecha o caixa de um funcionário automaticamente."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    try:
        # Busca o caixa
        caixa = await Caixa.get_or_none(id=form.caixa_id, usuario_id=current_user.id)

        if not caixa:
            raise HTTPException(
                status_code=404,
                detail="Caixa não encontrado.",
            )

        if not caixa.aberto:
            raise HTTPException(
                status_code=400,
                detail="Este caixa já está fechado.",
            )

        # Fecha o caixa automaticamente (calcula tudo)
        resultado = await CashController.fechar_caixa(caixa_id=form.caixa_id)

        return {"status": 200, "msg": "Caixa fechado com sucesso.", "caixa": resultado["caixa"], "detalhes": resultado["detalhes"]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@operador.get('/caixa/{caixa_id}/resumo')
async def resumo_caixa(
    caixa_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna o resumo do caixa antes do fechamento."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    try:
        # Verifica se o caixa pertence ao usuário
        caixa = await Caixa.get_or_none(id=caixa_id, usuario_id=current_user.id)
        if not caixa:
            raise HTTPException(status_code=404, detail="Caixa não encontrado.")

        if not caixa.aberto:
            raise HTTPException(status_code=400, detail="Este caixa já está fechado.")

        # Obtém os dados do caixa
        dados = await get_caixa_details(caixa_id)

        return {"status": 200, "dados": dados, "valor_sugerido_fechamento": caixa.saldo_atual}  # Saldo atual do caixa

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
