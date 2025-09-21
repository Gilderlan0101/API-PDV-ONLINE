from src.model.product import Produto
from fastapi import HTTPException


class ProductsInfos:
    '''
    Class responsavel por buscar informações dos produtos do usúario return dict or None
    '''

    def __init__(self, user_id: int):  # user_id: ID do usuario
        '''Sempre inicia as variaves vazias'''
        self.prducts = []  # informaçoes do stoque
        self.quantity = 0  # Quantiade em stoque
        self.price_total_stoke = float(0.00)  # Preço total em estoque
        self.user_id = user_id

    async def Quantity_products_stoke(self):
        '''Busca a quantiade de produtos em estoque'''
        try:

            global product

            # Bucando todos os produtos do usuario
            product = await Produto.filter(usuario_id=self.user_id).all()

            # Se a quantidade e maior que zero
            if len(product) > 0:
                for prod in product:
                    self.quantity += 1

                self.prducts.append({'quantity_in_stoke': self.quantity})

            else:  # Caso não encontre o valor continua sendo zero (0)
                self.quantity = 0

        except ValueError:
            if type(self.user_id) != int:
                var = self.Quantity_products_stoke(int(self.user_id))
            else:
                pass

        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Erro interno desconhecido: {e}')

        finally:

            return self.prducts

    async def price_of_all_stock(self):
        '''Calcularo valor total em stoke'''

        try:

            if product:
                for prod in product:

                    if self.quantity > 0:
                        self.price_total_stoke += prod.cost_price

                self.prducts.append({'price_stoke': round(self.price_total_stoke, 2)})
            else:
                return

        except Exception as e:

            raise HTTPException(status_code=500, detail=f'Erro interno desconhecido: {e}')

        finally:
            return self.prducts

    async def separating_products_by_category(self):
        try:

            if product:
                for prod in product:
                    self.prducts.append(
                        {
                            "name": prod.name,
                            "category": prod.group,
                            "stock": prod.stock,
                            "sale_price": prod.sale_price,
                            "active": prod.active
                        }
                    )



        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno desconhecido: {e}")

        finally:
            print(self.prducts)
            return self.prducts
