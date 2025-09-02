from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.transactions import in_transaction
from tortoise.functions import Count
from src.model.user import Usuario
from src.model.fornecedor import Fornecedor, SupplierStatus
from src.schemas.fornecedor.schemas_fornecedor import SupplierBase, SupplierListResponse, SupplierSummary
from src.auth.deps import get_current_user

router = APIRouter()


# ===============================
# Criar fornecedor
# ===============================
@router.post("/cadastra/", status_code=status.HTTP_201_CREATED)
async def create_fornecedor(
    fornecedor: SupplierBase,
    current_user: Usuario = Depends(get_current_user),
):
    if not current_user.id:
        raise HTTPException(status_code=400, detail="Usuário inválido")

    async with in_transaction() as conn:
        # Validar duplicidade de CNPJ/CPF
        if fornecedor.cnpj:
            exists = await Fornecedor.filter(cnpj=fornecedor.cnpj).using_db(conn).first()
            if exists:
                raise HTTPException(status_code=400, detail="CNPJ já cadastrado")

        if fornecedor.cpf:
            exists = await Fornecedor.filter(cpf=fornecedor.cpf).using_db(conn).first()
            if exists:
                raise HTTPException(status_code=400, detail="CPF já cadastrado")

        data = fornecedor.model_dump()
        data['site'] = str(data['site']) if data.get('site') else None

        register_forn = Fornecedor(
            **data,
            criado_em=datetime.now(ZoneInfo("America/Sao_Paulo")),
            atualizado_em=datetime.now(ZoneInfo("America/Sao_Paulo")),
            criado_por=str(current_user.id),
            atualizado_por=str(current_user.id),
            usuario_id=current_user.id
        )

        await register_forn.save(using_db=conn)

        return {
            "message": "Fornecedor cadastrado com sucesso!",
            "fornecedor_id": register_forn.id,
            "usuario_id": current_user.id,
        }


# ===============================
# Listar fornecedores
# ===============================
@router.get('/listar', response_model=SupplierListResponse)
async def list_fornecedores(
    current_user: Usuario = Depends(get_current_user),
    page: int = 1,
    size: int = 20
):
    offset = (page - 1) * size
    fornecedores = await Fornecedor.filter(usuario_id=current_user.id).offset(offset).limit(size)

    total_count = await Fornecedor.filter(usuario_id=current_user.id).count()

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
        total=total_count,
        page=page,
        pages=(total_count // size) + (1 if total_count % size > 0 else 0),
        data=data
    )


# ===============================
# Deletar fornecedor
# ===============================
@router.delete('/apagar/{fornecedor_id}', status_code=status.HTTP_200_OK)
async def delete_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user)
):
    async with in_transaction() as conn:
        fornecedor = await Fornecedor.filter(id=fornecedor_id, usuario_id=current_user.id).using_db(conn).first()
        if not fornecedor:
            raise HTTPException(status_code=404, detail="Fornecedor não encontrado")

        await fornecedor.delete(using_db=conn)
        return {"message": "Fornecedor deletado com sucesso!"}
