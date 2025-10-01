from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import Dict, Any
from tortoise.functions import Sum, Count

from src.utils.get_produtos_user import get_product_by_user
from src.model.product import Produto
from src.model.sale import Sales
from src.core.cache import client
import json


class Products:
    """
    Classe responsável por buscar informações detalhadas
    de um produto específico.
    """

    def __init__(self, user_id: int):
        self.user_id = user_id

    async def search_product(self, product_name: str) -> list[dict]:
        """
        Buscar um produto pelo nome.
        """
        if not isinstance(product_name, str):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Digite nome de um produto. Ex: Coca-Cola 2L.")

        try:
            cache_key = f"product:{self.user_id}:{product_name.lower()}"

            # 🔹 Verifica se já tem cache
            cache = client.get(cache_key)
            if cache:
                print("[CACHE] Produto encontrado no cache")
                return {"data": json.loads(cache)}

            # 🔹 Busca no banco
            product = await get_product_by_user(user_id=self.user_id, code=None, name=product_name)

            if product:
                product_data = {
                    "codigo": product.product_code,
                    "nome": product.name,
                    "preço": product.sale_price,
                }

                # 🔹 Salva no cache por 60 segundos
                client.setex(cache_key, 60, json.dumps(product_data))

                return [product_data]

            else:
                return [{"aviso": f"{product_name} não encontrado."}]

        except Exception as e:
            print(f"[ERRO search_product] {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno, tente novamente mais tarde.")

    async def observe_products_by_tickets(self, type_ticket: str, extra_type: Dict[list, Any] = None) -> dict[list, Any]:
        """
        Metodo responsavel por buscar produtos por tickets (Promoção, Novo...)

        parms:
            type_ticket: (str) Responsavel por pesquisar o tickets no banco.
            extra_type: (dict[list, Any] = None) Podemos usar para melhora o sistema de busca futuramente.
        """

        if not isinstance(type_ticket, str):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Digite nome de um ticket. Ex: Promoção.")

        try:

            cache_key = f"product:{self.user_id}:{type_ticket.lower()}"
            cache = client.get(cache_key)
            if cache:
                print('Produto encontrado em cache')
                return json.loads(cache)

            product = await Produto.filter(usuario_id=self.user_id, ticket=type_ticket).all()

            products_data = []
            if product:
                for prod in product:
                    products_data.append(
                        {
                            "codigo": prod.product_code,
                            "nome": prod.name,
                            "preço": prod.sale_price,
                            "preço": prod.ticket,
                        }
                    )

                client.setex(cache_key, 60, json.dumps(products_data))
                return products_data

            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sem resultado")

        except Exception as e:
            raise e

    async def calculate_average_ticket(self) -> float:
        """
        Calcula o Ticket Médio (Receita Total / Número de Transações Únicas)
        para todas as vendas do usuário.
        """

        try:
            # 1. Agrega a Receita Total e Conta o número de códigos de venda únicos (transações)
            aggregation = (
                await Sales.filter(usuario_id=self.user_id)
                .annotate(
                    # Soma de todos os total_price (Receita Bruta)
                    total_revenue=Sum('total_price'),
                    # Conta o número de códigos de vendas únicos (transações).
                    # Se 'sale_code' puder ser NULL, o COUNT(DISTINCT) é a forma mais segura.
                    num_transactions=Count('id', distinct=True),
                )
                .first()
            )

            # 2. Verifica e calcula
            if aggregation and aggregation.total_revenue is not None and aggregation.num_transactions > 0:

                total_revenue = aggregation.total_revenue
                num_transactions = aggregation.num_transactions

                # TICKET MÉDIO = Receita Total / Número de Transações
                ticket_medio = total_revenue / num_transactions

                return round(ticket_medio, 2)

            return 0.0  # Retorna zero se não houver vendas ou transações

        except Exception as e:
            print(f"Erro ao calcular o ticket médio: {e}")
            return 0.0
