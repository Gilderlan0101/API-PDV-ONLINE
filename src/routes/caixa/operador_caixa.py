# src/routes/caixa_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from src.auth.deps import get_current_user
from src.schemas.funcs.operador_cadastro import (
    AberturaCaixaRequest,
    CaixaFuncionarioCreate,
    CaixaFuncionarioUpdate,
)
from src.model.user import Usuario
from src.model.caixa import Caixa
from src.model.employee import Employees

from src.controllers.caixa.cash_controller import CashController

operador = APIRouter()

# --- Rota de Abertura de Caixa ---

@operador.post('/abertura')
async def abertura_caixa(
    request: AberturaCaixaRequest,
    current_user: Usuario = Depends(get_current_user),
):
    """Abre o caixa para o próprio funcionário."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    # Opção 1 (Recomendada): Filtrar usando o objeto de relacionamento
    # A ORM cuida do filtro pelo ID automaticamente.
    funcionario = await Employees.filter(usuario=current_user).first()
    
    # Opção 2 (Alternativa): Filtrar usando o nome da coluna no banco de dados
    # Isso também funciona e pode ser útil para depuração.
    # funcionario = await Employees.filter(usuario_id=current_user.id).first()

    if not funcionario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não é um funcionário válido ou não encontrado."
        )

    print(f"Tentando abrir caixa para usuario_id: {current_user.id}, funcionario_id: {funcionario.id}")
    
    try:
        caixa = await CashController.abrir_caixa(
            usuario_id=current_user.id,
            funcionario_id=funcionario.id,
            saldo_inicial=request.saldo_inicial,
            nome=funcionario.nome or f"Caixa {funcionario.id} - {current_user.company_name}",
        )
        return {"status": 200, "msg": "Caixa aberto com sucesso.", "caixa": caixa}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

---

### Outras Rotas (Completas e Inalteradas)

```python
@operador.get('/caixa/{caixa_id}/resumo')
async def resumo_caixa(
    caixa_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna o resumo do caixa antes do fechamento."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não autenticado")

    try:
        caixa = await Caixa.get_or_none(id=caixa_id, usuario_id=current_user.id)
        if not caixa:
            raise HTTPException(status_code=404, detail="Caixa não encontrado.")

        if not caixa.aberto:
            raise HTTPException(status_code=400, detail="Este caixa já está fechado.")

        dados = await CashController.get_caixa_details(caixa_id)

        return {"status": 200, "dados": dados, "valor_sugerido_fechamento": caixa.saldo_atual}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@operador.get('/infos/caixas')
async def information_from_all_cashiers(current_user: Usuario = Depends(get_current_user)):

    if not current_user.id:
        raise HTTPException(status_code=404, detail='Usuario não encontrado.')

    user = await Usuario.filter(id=current_user.id).first()

    cashs = await Caixa.filter(usuario_id=user.id).all()

    infos = []
    if len(cashs) > 0:

        for data in cashs:
            if data.aberto:

                infos.append({
                'Nome': data.nome,
                'ID': data.id,
                'Aberto': data.aberto,
                'Saldo_atual': data.saldo_atual
                })

        return infos

    else:
        print('nada encontrado')
        raise HTTPException(status_code=404, detail='dados não encontrado.')