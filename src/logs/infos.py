import logging
import os
import sys
from typing import Final  # Importar Final para tipagem mais clara de constantes

# --- 1. Configuração de Variáveis Constantes ---

LOG_NAME: Final[str] = 'error_module'
# Define o arquivo de log dois níveis acima do diretório atual (raiz do projeto)
LOG_FILE: Final[str] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'system.log'))
# Define o formato de saída do log
LOG_FORMAT: Final[str] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# --- 2. Criação Segura do Arquivo de Log e Diretório ---

# Obtém apenas o diretório do caminho do arquivo
log_dir = os.path.dirname(LOG_FILE)

# Cria o diretório se ele não existir
if log_dir and not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir, exist_ok=True)
        # Note: Não usamos o logger aqui, pois ele ainda está sendo configurado.
        print(f"✅ Diretório de log criado: {log_dir}")
    except OSError as e:
        print(f"❌ Erro ao criar o diretório '{log_dir}': {e}")

# Cria o arquivo de log (somente se não existir) e escreve uma linha inicial
try:
    with open(LOG_FILE, 'x') as files_log:
        files_log.write('INÍCIO DA SESSÃO DE LOG\n')
except FileExistsError:
    # O arquivo já existe, apenas ignoramos
    pass
except Exception as e:
    # Trata outros erros, como permissão de escrita
    print(f"❌ Ocorreu um erro ao inicializar o arquivo de log: {e}")


# --- 3. Função de Configuração Principal ---

def setup_logging() -> logging.Logger:
    """
    Configura o logger para enviar logs para o console (INFO+) e para o arquivo (DEBUG+).
    Retorna a instância do logger configurado.
    """
    # 1. Obter o logger
    logger = logging.getLogger(LOG_NAME)
    # Define o nível de processamento mais baixo possível para o logger (o que for DEBUG ou superior)
    logger.setLevel(logging.DEBUG)
    
    # IMPORTANTE: Desativa a propagação para o logger raiz para evitar logs duplicados
    logger.propagate = False 

    # 2. Formato do Log
    formatter = logging.Formatter(LOG_FORMAT)

    # 3. Adicionar Handlers (se ainda não tiverem sido adicionados)
    if not logger.handlers:
        
        # --- Handler para Console (StreamHandler) ---
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        # Nível mínimo para aparecer no terminal
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # --- Handler para Arquivo (FileHandler) ---
        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setFormatter(formatter)
        # Nível mínimo para ir para o arquivo (geralmente DEBUG para detalhes)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    return logger

# --- 4. Exposição do Logger Configurado ---

# A chamada da função é feita uma única vez ao importar o módulo
LOGGER = setup_logging()

# Exemplo de teste rápido (será logado no console e no arquivo)
LOGGER.info("Configuração de log concluída e pronta para uso.")

__all__ = ['LOGGER']
