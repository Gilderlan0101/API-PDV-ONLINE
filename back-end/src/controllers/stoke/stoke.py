def products_in_stoke(product):
    try:
        all_products = []
        for pdc in product:
            all_products.append(
                {
                    'product_code': pdc['product_code'],
                    'name': pdc['name'],
                    'stoke': pdc['stoke'],
                    'fabricator': pdc['fabricator'],
                    'cost_price': pdc['cost_price'],
                    'price_uni': pdc['price_uni'],
                    'sale_price': pdc['sale_price'],
                    'supplier': pdc['supplier'],
                    'lot_bar_code': pdc['lot_bar_code'],
                    'image_url': pdc['image_url'],
                }
            )

        return all_products

    except (ValueError, KeyError) as Error:
        return {'messagem': Error}
