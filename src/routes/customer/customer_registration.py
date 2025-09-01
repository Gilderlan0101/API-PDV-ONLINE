from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.model.customers import Customer, ZoneInfo
from src.schemas.customers.schema_customers import (
    GetCustomers,
    SchemasCustomer,
    SchemasCustomerCreditUpdate
)

customers = APIRouter(tags=["Customers"])

# ===============================
# Criar cliente
# ===============================
@customers.post('/create-customer')
async def create_customer(
    form: SchemasCustomer,
    current_user: Usuario = Depends(get_current_user),
):
    # Verifica se já existe cliente com o mesmo CPF
    existing_customer = await Customer.filter(cpf=form.cpf).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="⚠️ Cliente já cadastrado com este CPF."
        )

    # Cria o cliente
    customer_register = await Customer.create(
        full_name=form.full_name,
        birth_date=form.birth_date,
        cpf=form.cpf,
        mother_name=form.mother_name,
        road=form.road,
        house_number=form.house_number,
        neighborhood=form.neighborhood,
        city=form.city,
        tel=form.tel,
        cep=form.cep,
        credit=form.credit,
        due_date=form.due_date,
        status=form.status.value,  # Enum para string
        usuario_id=current_user.id
    )

    return {
        "message": "✅ Cliente cadastrado com sucesso!",
        "customer": customer_register
    }

# ===============================
# Listar clientes
# ===============================
@customers.get("/list-customer", response_model=List[GetCustomers])
async def list_customer(current_user: Usuario = Depends(get_current_user)):
    customers_list = await Customer.filter(usuario_id=current_user.id).all()
    return customers_list or []

# ===============================
# Atualizar crédito/gasto do cliente
# ===============================
@customers.put("/update-customer-credit")
async def update_customer_credit(
    update_data: SchemasCustomerCreditUpdate,
    cpf: str = Query(..., description="CPF do cliente"),
    current_user: Usuario = Depends(get_current_user),
):
    customer = await Customer.filter(cpf=cpf, usuario_id=current_user.id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado pelo CPF"
        )

    if update_data.current_balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo não pode ser negativo"
        )

    if update_data.current_balance > customer.credit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gasto acumulado (R$ {update_data.current_balance:,.2f}) excede o crédito total (R$ {customer.credit:,.2f})"
        )

    customer.current_balance = update_data.current_balance
    customer.updated_at = datetime.now(ZoneInfo("America/Sao_Paulo"))
    await customer.save()

    return GetCustomers(
        full_name=customer.full_name,
        cpf=customer.cpf,
        credit=customer.credit,
        current_balance=customer.current_balance,
        total_spent=customer.current_balance,
        due_date=customer.due_date,
        status=customer.status
    )

# ===============================
# Deletar cliente
# ===============================
@customers.delete("/delete-customer/{customer_id}")
async def delete_customer(
    customer_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    customer = await Customer.filter(id=customer_id, usuario_id=current_user.id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    await customer.delete()
    return {"message": "Cliente excluído com sucesso!"}
