from typing import Optional
from sqlmodel import SQLModel, Field


# ========================
# 🔹 Schema Caixa Funcionário
# ========================
class CaixaFuncionarioCreate(SQLModel):
    funcionario_id: int = Field(..., description="ID do funcionário que está abrindo o caixa")
    valor_abertura: float = Field(..., description="Valor que o funcionário informou na abertura do caixa")


# ========================
# 🔹 Schema de Atualização do Caixa (Fechamento)
# ========================
class CaixaFuncionarioUpdate(SQLModel):
    caixa_id: int = Field(..., description="ID do caixa a ser fechado")
