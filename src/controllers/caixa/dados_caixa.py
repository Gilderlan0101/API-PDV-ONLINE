from typing import Dict, Any
from src.model.caixa import Caixa
from src.model.sale import Sales


async def get_caixa_details(funcionario_id: int, caixa_id: int) -> Dict[str, Any]:
    """
    Retorna o resumo do caixa de um funcionário:
    - Lista de vendas
    - Total por tipo de pagamento
    - Valor total das vendas
    - Diferença
    """
    # Busca o caixa
    caixa = await Caixa.filter(id=caixa_id, funcionario_id=funcionario_id).first()
    if not caixa:
        raise ValueError("Caixa não encontrado.")

    # Busca todas as vendas do funcionário desde a abertura do caixa
    vendas = await Sales.filter(funcionario_id=funcionario_id, criado_em__gte=caixa.criado_em).all()

    # Inicializa totais
    total_sistema = 0.0
    total_por_pagamento: Dict[str, float] = {}

    for venda in vendas:
        total_sistema += venda.total_price
        # Supondo que exista campo payment_type na tabela Sales
        tipo_pagamento = getattr(venda, "payment_type", "dinheiro")
        total_por_pagamento[tipo_pagamento] = total_por_pagamento.get(tipo_pagamento, 0) + venda.total_price

    # Calcula diferença (se fechamento já foi realizado)
    diferenca = None
    if hasattr(caixa, "valor_fechamento") and caixa.valor_fechamento is not None:
        diferenca = caixa.valor_fechamento - total_sistema

    return {
        "caixa_id": caixa.id,
        "funcionario_id": funcionario_id,
        "valor_abertura": getattr(caixa, "saldo_inicial", 0),
        "valor_fechamento": getattr(caixa, "valor_fechamento", None),
        "valor_sistema": total_sistema,
        "diferenca": diferenca,
        "vendas": vendas,
        "total_por_pagamento": total_por_pagamento,
    }
