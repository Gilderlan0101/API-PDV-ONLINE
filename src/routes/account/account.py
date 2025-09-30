from fastapi import APIRouter, Body, Depends, HTTPException, status
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.model.employee import Employees
from src.routes.registre import get_hashed_password
from src.schemas.funcs.registre_funcs import EmployeesCreate

employees_router = APIRouter(prefix='/auth', tags=['Autenticação'])

# Tamananho da senha que o funcionario deve conte
PASSWORD_LENGTH = 4


@employees_router.post('/funcs')
async def create_employees(
    func_data: EmployeesCreate = Body(...),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cadastra um novo funcionário.

    Args:
        func_data (EmployeesCreate): Dados do funcionário.
        current_user: (Usuario): Usuário autenticado que está criando um funcionário.

    Raises:
        HTTPException: Se não estive autenticado, email já cadastrado ou seha inválida.


    Returns:
        dict: Mensagem de sucesso e dados do funcionário criado.
    """

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificando se esse email já existe
    existing = await Employees.filter(email=func_data.email).first()

    if existing:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email já cadastrado.')

    # Valida senha de 4 dígitos
    if len(str(func_data.senha)) != PASSWORD_LENGTH:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Senha deve ter {PASSWORD_LENGTH} dígitos.")

    # Criando Hash da senha
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
