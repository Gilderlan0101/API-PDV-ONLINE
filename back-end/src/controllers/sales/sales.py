import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
)
from controllers.stoke import products_in_stoke


class GenerateSales:
    def __init__(
        self,
        product_name: str,
        payment_method: str,
        amount: int,
        observation: None,
    ):
        self.product_name = product_name.strip()
        self.payment_method = str(payment_method).strip()
        self.observation = observation
        self.amount = amount

        self.product_data = self.checkstok()

        if self.product_data:
            self.value = self.product_data.get('price')
        else:
            self.value = 0.0

    def validate_sales(self) -> dict | bool:

        if not self.product_name or not self.value or not self.payment_method:
            return {
                'status': False,
                'data': {
                    'product_name': None,
                    'value': None,
                    'payment_method': None,
                    'observation': self.observation,
                },
            }
        else:
            return {
                'status': True,
                'data': {
                    'stoke': self.product_data.get('stoke'),
                    'product_name': self.product_data.get('product')
                    if self.product_data
                    else None,
                    'value': self.value,
                    'payment_method': self.payment_method,
                    'observation': self.observation,
                },
            }

    def checkstok(self):
        """Verifica se o produto está no estoque"""
        all_products = products_in_stoke(stoke)

        for i, product in enumerate(all_products):
            if product.get('name', '').lower() == self.product_name.lower():

                return {
                    'index': i,  # importante!
                    'stoke': product.get('stoke'),
                    'product_code': product.get('product_code'),
                    'product': product.get('name'),
                    'price': product.get('sale_price'),
                    'lot_bar_code': product.get('lot_bar_code'),
                    'image_url': product.get('image_url'),
                }

        return None


class GeneratingNote(GenerateSales):

    customer_items = []

    def __init__(self, product_name, payment_method, amount, observation):
        super().__init__(product_name, payment_method, amount, observation)

        self.amount = amount

    @property
    def customernote(self):
        """Atualiza o estoque do produto e retorna uma nota"""
        result = self.validate_sales()

        if result['status'] and self.product_data:
            index = self.product_data.get('index')
            if index is not None:
                old_stock = stoke[index]['stoke']
                new_stock = max(old_stock - self.amount, 0)
                stoke[index]['stoke'] = new_stock  # atualiza o estoque real
                print(
                    f'[OK] Estoque atualizado de {old_stock} para {new_stock}'
                )
                print('#' * 20, 'NOTA', '#' * 20)

                self.customer_items.append(
                    {
                        'product': stoke[index]['name'],
                        'price': stoke[index]['sale_price'],
                        'amount': self.amount,
                        'total': round(
                            self.amount * stoke[index]['sale_price'], 2
                        ),
                    }
                )

            else:
                print('[ERRO] Produto não encontrado no estoque original.')
        else:
            print('[ERRO] Venda inválida. Produto não atualizado.')

    @classmethod
    def show_items(cls):
        """Exibe os itens da nota fiscal"""
        total_gerado = 0
        nota_formatada = []

        print('\n📦 Itens da Nota Fiscal:')
        for item in cls.customer_items:
            total_gerado += item['total']
            nota_formatada.append(
                {
                    'Produto': item['product'],
                    'Quantidade': item['amount'],
                    'Preço Unitário': f"R${item['price']}",
                    'Total': f"R${item['total']}",
                }
            )

        nota_formatada.append({'TOTAL GERAL': f'R${round(total_gerado, 2)}'})
        return nota_formatada
