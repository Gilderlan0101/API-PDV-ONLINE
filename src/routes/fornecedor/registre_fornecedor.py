from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from src.conf.database import engine
from src.model.user import Usuario
from src.model.user import Fornecedor
from src.schemas.fornecedor.schemas_fornecedor import SupplierCreate, SupplierListResponse, SupplierSummary
from src.auth.deps import get_current_user

router = APIRouter()

@router.post("/cadastra/", status_code=status.HTTP_201_CREATED)
async def create_fornecedor(
    fornecedor: SupplierCreate,
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user.id:
        raise HTTPException(status_code=400, detail="Usuário inválido")

    with Session(engine) as session:
        try:
            # Validar duplicidade de CNPJ/CPF
            if fornecedor.cnpj:
                exists = session.exec(
                    select(Fornecedor).where(Fornecedor.cnpj == fornecedor.cnpj)
                ).first()
                if exists:
                    raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

            if fornecedor.cpf:
                exists = session.exec(
                    select(Fornecedor).where(Fornecedor.cpf == fornecedor.cpf)
                ).first()
                if exists:
                    raise HTTPException(status_code=400, detail="CPF já cadastrado")
                
            
            data = fornecedor.model_dump()
            data['site'] = str(data['site']) if data.get('site') else None

            # Preparar registro
            register_forn = Fornecedor(
               **data,
                criado_em=datetime.now(),
                atualizado_em=datetime.now(),
                criado_por=current_user.id,
                atualizado_por=current_user.id,
                usuario_id=current_user.id
            )

            session.add(register_forn)
            session.commit()
            session.refresh(register_forn)

            return {
                "message": "Fornecedor cadastrado com sucesso!",
                "fornecedor_id": register_forn.id,
                "usuario_id": current_user.id,
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=f"Erro: {e}")
from sqlmodel import select, func

@router.get('/listar', response_model=SupplierListResponse)
async def list_fornecedores(
    current_user: Usuario = Depends(get_current_user),
    page: int = 1,
    size: int = 20
):
    with Session(engine) as session:
        # Query base para fornecedores do usuário
        query = select(Fornecedor).where(Fornecedor.usuario_id == current_user.id)
        fornecedores = session.exec(
            query.offset((page - 1) * size).limit(size)
        ).all()

        # Contagem total
        total_query = select(func.count()).select_from(Fornecedor).where(Fornecedor.usuario_id == current_user.id)
        total = session.exec(total_query).one()

        data = [
            SupplierSummary(
                id=f.id,
                razao_social=f.razao_social,
                nome_fantasia=f.nome_fantasia,
                cnpj=f.cnpj,
                cpf=f.cpf,
                email=f.email,
                status=f.status,
                cidade=f.endereco.get('cidade') if f.endereco else "",
                uf=f.endereco.get('uf') if f.endereco else ""
            )
            for f in fornecedores
        ]

        return SupplierListResponse(
            success=True,
            total=total,
            page=page,
            pages=(total // size) + (1 if total % size > 0 else 0),
            data=data
        )


@router.delete('/apagar/{fornecedor_id}', status_code=status.HTTP_200_OK)
async def delete_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user)
):
    with Session(engine) as session:
        fornecedor = session.get(Fornecedor, fornecedor_id)

        if not fornecedor or fornecedor.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

        session.delete(fornecedor)
        session.commit()

        return {"message": "Fornecedor deletado com sucesso!"}