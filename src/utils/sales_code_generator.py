import random
import string


def gerar_codigo_venda(size: int = 6) -> str:
    """Gera um código aleatório para a venda."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=size))
