def check_replacement(stock_control):
    response = []

    for code, product in stock_control.items():
        current_stock = product['stoke'] - product['sold']
        if current_stock <= product['minimum_required']:
            response.append(
                {
                    'product_code': code,
                    'product_name': product['name'].capitalize(),
                    'current_stock': current_stock,
                    'status': 'Reposição necessária',
                    'alert': f"⚠️ Produto '{product['name']}' abaixo do mínimo!",
                }
            )
        else:
            response.append(
                {
                    'product_code': code,
                    'product_name': product['name'].capitalize(),
                    'current_stock': current_stock,
                    'status': 'Estoque OK',
                }
            )

    return response
