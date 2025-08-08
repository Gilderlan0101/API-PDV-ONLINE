import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Devemos busca a validade do produto diretamente do banco
DATA_EXPIRED = '10/05/2025'


def expired_products(obj):
    try:
        all_expireds_products = []
        total_value = 0

        for product in obj:
            if product['date_expired'] == DATA_EXPIRED:
                all_expireds_products.append(
                    {
                        'name': product['name'],
                        'price': product['price_uni'],
                        'expired_date': product['date_expired'],
                        'valor_total': product['price_uni'],
                    }
                )
                total_value += product['price_uni']

        return {'products': all_expireds_products, 'total_value': total_value}

    except (ValueError, KeyError) as erro:
        return {'message': str(erro)}
