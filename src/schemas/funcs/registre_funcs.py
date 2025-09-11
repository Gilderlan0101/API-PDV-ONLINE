from pydantic import BaseModel
from typing import Optional

class FuncionarioCreate(BaseModel):
    nome: str
    cargo: str
    email: str
    senha: str
    telefone: str
    ativo: bool


class OutputFormat(BaseModel):
    nome: str
    cargo: str
    email: str
    telefone: Optional[str] = None
    ativo: bool


