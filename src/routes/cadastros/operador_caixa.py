from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlmodel import Session, select

from src.controllers.caixa.dados_caixa import get_caixa_details

from src.schemas.funcs.operador_cadastro import CaixaFuncionarioCreate, CaixaFuncionarioUpdate
from src.model.user import Usuario
from src.model.caixa import Caixa

operador = APIRouter(
    prefix='/auth',
    tags=['Autenticação']
)

from fastapi import APIRouter, Depends, HTTPException, status, Body
from src.auth.deps import get_current_user
from src.schemas.funcs.operador_cadastro import CaixaFuncionarioCreate, CaixaFuncionarioUpdate
from src.model.user import Usuario
from src.model.caixa import Caixa

operador = APIRouter(
    prefix='/auth',
    tags=['Autenticação']
)

@operador.post('/abertura')
async def abertura_caixa(
    form: CaixaFuncionarioCreate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """Abre o caixa para um funcionário."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    # Verifica se o funcionário já tem um caixa aberto
    caixa_existente = await Caixa.filter(funcionario_id=form.funcionario_id, aberto=True).first()
    if caixa_existente:
        raise HTTPException(status_code=400, detail='Este funcionário já possui um caixa aberto.')

    # Cria o caixa
    novo_caixa = await Caixa.create(
        funcionario_id=form.funcionario_id,
        saldo_inicial=form.valor_abertura,
        saldo_atual=form.valor_abertura,
        aberto=True,
        usuario_id=current_user.id,
        nome=f"Caixa {form.funcionario_id} - {current_user.company_name}"
    )

    return {
        "status": 200,
        "msg": "Caixa aberto com sucesso.",
        "caixa": novo_caixa
    }


@operador.post('/fechamento')
async def fechamento_caixa(
    form: CaixaFuncionarioUpdate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """Fecha o caixa de um funcionário."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    # Busca o caixa aberto
    caixa_aberto = await Caixa.filter(funcionario_id=current_user.id, aberto=True).first()
    if not caixa_aberto:
        raise HTTPException(status_code=404, detail="Nenhum caixa aberto encontrado para este funcionário.")

    # Atualiza valores
    caixa_aberto.saldo_atual = form.valor_fechamento
    caixa_aberto.aberto = False
    await caixa_aberto.save()

    return {
        "status": 200,
        "msg": "Caixa fechado com sucesso.",
        "caixa": caixa_aberto
    }
