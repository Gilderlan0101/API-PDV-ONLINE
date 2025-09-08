# src/conf/database.py
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
sqlite_file_name = os.getenv("DATABASE_URL") or "app.db"

# Se não vier no formato correto, monta
if not sqlite_file_name.startswith("sqlite://"):
    sqlite_url = f"sqlite://{sqlite_file_name}"
else:
    sqlite_url = sqlite_file_name

# Configuração do Tortoise ORM
TORTOISE_ORM = {
    "connections": {"default": sqlite_url},
    "apps": {
        "models": {
            "models": [
                "src.model.user",
                "src.model.employee",
                "src.model.customers",
                "src.model.caixa",
                "src.model.cashmovement",
                "src.model.sale",
                "src.model.carItems",
                "src.model.product",
                "src.model.fornecedor",
                "src.model.membros",
                "src.model.cnpjCache",
                "src.model.tickets",  # corrigido para plural
                # "aerich.models",       # obrigatório se for usar migrações com Aerich
            ],
            "default_connection": "default",
        }
    },
}
