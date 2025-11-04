# src/conf/database.py
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Dados de conexão — você pode mover para o .env se quiser
DB_USER = os.getenv("DB_USER", "naht1344_usuairos")
DB_PASS = os.getenv("DB_PASS", "3QzMZKGSGmJnchBd")
DB_HOST = os.getenv("DB_HOST", "localhost")  # ou o IP do servidor
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "naht1344_usuairos")

# Montar URL de conexão MySQL
mysql_url = f"mysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuração do Tortoise ORM
TORTOISE_ORM = {
    "connections": {"default": mysql_url},
    "apps": {
        "models": {
            "models": [
                "src.model.user",
                "src.model.employee",
                "src.model.customers",
                "src.model.caixa",
                "src.model.cashmovement",
                "src.model.sale",
                "src.model.partial",
                "src.model.carItems",
                "src.model.product",
                "src.model.fornecedor",
                "src.model.membros",
                "src.model.cnpjCache",
                "src.model.tickets",
                "src.model.delivery",
                "src.model.pix",
            ],
            "default_connection": "default",
        }
    },
}

# Debug opcional — mostrar URL de conexão (sem senha)
print(f"Conectando ao banco MySQL '{DB_NAME}' em {DB_HOST}:{DB_PORT}")
