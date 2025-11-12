from pydantic import BaseModel, ConfigDict
from datetime import datetime

# --- Esquema Pydantic (Exemplo) ---
# Adicione este modelo em um arquivo de schemas ou no topo da sua rota/serviço


class PixAccountResponse(BaseModel):
    id: int
    usuario_id: int
    full_name: str
    key_pix: str
    city: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Configuração para ler dados de um objeto de ORM
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2
    # class Config:
    #    orm_mode = True # Pydantic v1


class PixAccountsList(BaseModel):
    count: int
    accounts: list[PixAccountResponse]
