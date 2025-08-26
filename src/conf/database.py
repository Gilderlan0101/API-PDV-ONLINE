# src/conf/database.py
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from src.model.user import Usuario,  Membro, CNPJCache, Fornecedor
from src.model.product import Produto
from src.model.sale import Sales



load_dotenv()

# Banco SQLite padrão (se não tiver .env configurado)
sqlite_file_name = os.getenv("DATABASE_URL", "app.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Configuração do SQLite
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


# Criar tabelas automaticamente
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Dependência para abrir uma sessão no FastAPI
def get_session():
    with Session(engine) as session:
        yield session
