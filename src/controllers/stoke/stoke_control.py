import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from src.conf.database import engine
from src.model.product import Produto
from src.model.user import Usuario
from sqlmodel import Session, select


def get_user(user_id: int) -> Usuario | None:
    """Retorna o objeto Usuario ou None."""
    with Session(engine) as session:
        return session.exec(select(Usuario).where(Usuario.id == user_id)).first()


def get_user_products(user: Usuario) -> list[dict]:
    """
    Retorna todos os produtos de um usuário como lista de dicionários.
    """
    if user is None:
        print('❌ Usuário não encontrado!')
        return []

    with Session(engine) as session:
        produtos = session.exec(
            select(
                Produto.id,
                Produto.name,
                Produto.stock,
                Produto.stoke_min,
                Produto.stoke_max,
                Produto.date_expired,
                Produto.price_uni,
            ).where(  # type: ignore
                Produto.usuario_id == user.id
            )  # type: ignore
        ).all()

    return [
        {
            'id': p[0],
            'name': p[1],
            'stock_atual': p[2],
            'stock_min': p[3],
            'stock_max': p[4],
            'date_expired': p[5],
            'price_uni': p[6],
        }
        for p in produtos
    ]


def check_replacement(produtos: list[dict]) -> list[dict]:
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


def expired_products(produtos: list[dict]) -> dict:
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
            data_validade = (
                product['date_expired'].date() if product['date_expired'] else None
            )
            if not data_validade:
                continue

            dias_restantes = (data_validade - data_atual).days
            valor_lote = product['stock_atual'] * product['price_uni']

            if dias_restantes < 0:
                # Produto já venceu
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
                # Produto vencendo em até 10 dias
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


def gerar_relatorio_completo(user_id: int) -> dict:
    """
    Gera um relatório completo unindo reposição e validade.
    """
    user = get_user(user_id)
    produtos_usuario = get_user_products(user)  # type: ignore

    return {
        'estoque': check_replacement(produtos_usuario),
        'validade': expired_products(produtos_usuario),
    }
