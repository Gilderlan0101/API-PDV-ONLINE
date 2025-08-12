from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from src.auth.deps import get_current_user
from src.conf.database import engine
from src.model.user import Usuario
from src.model.employee import Employees
from src.routes.registre import get_hashed_password
from src.schemas.funcs.registre_funcs import FuncionarioCreate


class RegisteEmpreg:
    def __init__(self):
        
        self.router = APIRouter(
            prefix='/auth',
            tags=['Autenticação'],
        )
        
        self.startup_route()
        
    def startup_route(self):
        """Esta rota cadastra um fucionarios"""
        
        @self.router.post('/funcs')
        def funcs(
            current_user: Usuario = Depends(get_current_user),
            func_data: FuncionarioCreate = Body(...)
        ):
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário não autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                ) 
            
            # Verifica se o email já existe
            with Session(engine) as session:
                if session.exec(
                    select(Employees).where(Employees.email == func_data.email)
                ).first():
                    raise HTTPException(status_code=400,  detail='Email já cadastrado.')
              
            # Criptografa a senha
             # Criptografa a senha (deve garantir que pwd tenha 4 caracteres)
            if len(func_data.senha) != 4:
                raise HTTPException(status_code=400, detail="Senha deve ter 4 dígitos.")
            hashed_password = get_hashed_password(func_data.senha)

            # Cria conta do fucionario
            # Cria o funcionário
            new_func = Employees(
                nome=func_data.nome,
                cargo=func_data.cargo,
                email=func_data.email,
                senha=hashed_password,
                telefone=func_data.telefone,
                ativo=True,
                usuario_id=current_user.id  # liga ao usuário logado
        )

            # Adiciona e salva no banco
            session.add(new_func)
            session.commit()
            session.refresh(new_func)
            print('Novo registro')

            return {"msg": "Funcionário cadastrado com sucesso", "funcionario": new_func}
                 