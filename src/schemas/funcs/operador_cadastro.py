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
    valor_fechamento: float = Field(..., description="Valor contado no fechamento")
    valor_sistema: float = Field(..., description="Valor registrado pelo sistema")
    diferenca: Optional[float] = Field(None, description="Diferença entre contado e sistema")
    aberto: bool = Field(default=False, description="Status do caixa (False = fechado)")
