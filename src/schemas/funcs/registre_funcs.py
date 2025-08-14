from pydantic import BaseModel


class FuncionarioCreate(BaseModel):
    nome: str
    cargo: str
    email: str
    senha: str
    telefone: str
    ativo: bool
