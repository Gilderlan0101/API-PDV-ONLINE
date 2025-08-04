# src/conf/database.py
from sqlmodel import create_engine, SQLModel
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

# Banco SQLite para desenvolvimento
sqlite_file_name = os.getenv('DATABASE_URL', 'app.db')
sqlite_url = f'sqlite:///{sqlite_file_name}'
connect_args = {'check_same_thread': False}

engine = create_engine(sqlite_url, connect_args=connect_args)

# Criando o banco de dados e suas tabelas
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
