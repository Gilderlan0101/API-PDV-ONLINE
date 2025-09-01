from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict

from tortoise.exceptions import DoesNotExist

from src.model.user import Usuario
from src.model.product import Produto


async def get_user(user_id: int) -> Usuario | None:
    """Retorna o objeto Usuario ou None."""
    try:
        return await Usuario.get(id=user_id)
    except DoesNotExist:
        return None


async def get_user_products(user: Usuario) -> List[Dict]:
    """
    Retorna todos os produtos de um usuário como lista de dicionários.
    """
    if user is None:
        print('❌ Usuário não encontrado!')
        return []

    produtos = await Produto.filter(usuario_id=user.id).all()

    return [
        {
            'id': p.id,
            'name': p.name,
            'stock_atual': p.stock,
            'stock_min': p.stoke_min,
            'stock_max': p.stoke_max,
            'date_expired': p.date_expired,
            'price_uni': p.price_uni,
        }
        for p in produtos
    ]


def check_replacement(produtos: List[Dict]) -> List[Dict]:
    """
    Verifica estoque e retorna status de reposição.
    """
    status_estoque = []
    for product in produtos:
        stock_atual = product['stock_atual']
        stock_min = product['stock_min']

        if stock_atual <= stock_min:
            status = {
                'product_name': product['name'].capitalize(),
                'current_stock': stock_atual,
                'status': 'Reposição necessária',
                'alert': f"⚠️ Produto '{product['name']}' abaixo do mínimo!",
            }
        else:
            status = {
                'product_name': product['name'].capitalize(),
                'current_stock': stock_atual,
                'status': 'Estoque OK',
            }

        status_estoque.append(status)

    return status_estoque


def expired_products(produtos: List[Dict]) -> Dict:
    """
    Retorna produtos vencendo e vencidos,
    com valor total de perdas e valor em risco.
    """
    try:
        data_atual = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        produtos_vencendo = []
        produtos_vencidos = []
        valor_total_vencido = 0
        valor_total_potencial = 0

        for product in produtos:
            data_validade = product['date_expired'].date() if product['date_expired'] else None
            if not data_validade:
                continue

            dias_restantes = (data_validade - data_atual).days
            valor_lote = product['stock_atual'] * product['price_uni']

            if dias_restantes < 0:
                produtos_vencidos.append(
                    {
                        'name': product['name'],
                        'expired_date': data_validade.strftime('%Y-%m-%d'),
                        'stock': product['stock_atual'],
                        'price': product['price_uni'],
                        'valor_lote': valor_lote,
                        'dias_restantes': dias_restantes,
                        'alert': f"❌ Produto '{product['name']}' já venceu há {abs(dias_restantes)} dias!",
                    }
                )
                valor_total_vencido += valor_lote

            elif dias_restantes <= 10:
                produtos_vencendo.append(
                    {
                        'name': product['name'],
                        'expired_date': data_validade.strftime('%Y-%m-%d'),
                        'stock': product['stock_atual'],
                        'price': product['price_uni'],
                        'valor_lote': valor_lote,
                        'dias_restantes': dias_restantes,
                        'alert': f"⚠️ Produto '{product['name']}' vence em {dias_restantes} dias!",
                    }
                )
                valor_total_potencial += valor_lote

        return {
            'produtos_vencendo': produtos_vencendo,
            'produtos_vencidos': produtos_vencidos,
            'valor_total_vencido': valor_total_vencido,
            'valor_total_potencial': valor_total_potencial,
        }

    except Exception as erro:
        return {'message': str(erro)}


async def gerar_relatorio_completo(user_id: int) -> Dict:
    """
    Gera um relatório completo unindo reposição e validade.
    """
    user = await get_user(user_id)
    produtos_usuario = await get_user_products(user)

    return {
        'estoque': check_replacement(produtos_usuario),
        'validade': expired_products(produtos_usuario),
    }
