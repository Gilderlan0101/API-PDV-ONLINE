from fastapi import APIRouter, Body, Depends, HTTPException, status
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.model.employee import Employees
from src.routes.registre import get_hashed_password
from src.schemas.funcs.registre_funcs import FuncionarioCreate

employees_router = APIRouter(prefix='/auth', tags=['Autenticação'])


@employees_router.post('/funcs')
async def create_funcionario(
    func_data: FuncionarioCreate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """Cadastra um novo funcionário"""

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica se o email já existe
    existing = await Employees.filter(email=func_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email já cadastrado.')

    # Valida senha de 4 dígitos
    if len(func_data.senha) != 4:
        raise HTTPException(status_code=400, detail="Senha deve ter 4 dígitos.")
    hashed_password = get_hashed_password(func_data.senha)

    # Cria funcionário
    new_func = await Employees.create(
        nome=func_data.nome,
        cargo=func_data.cargo,
        email=func_data.email,
        senha=hashed_password,
        telefone=func_data.telefone,
        ativo=True,
        usuario_id=current_user.id,
    )

    return {
        "msg": "Funcionário cadastrado com sucesso",
        "funcionario": {
            "id": new_func.id,
            "nome": new_func.nome,
            "cargo": new_func.cargo,
            "email": new_func.email,
            "telefone": new_func.telefone,
            "ativo": new_func.ativo,
            "usuario_id": new_func.id,
        },
    }
