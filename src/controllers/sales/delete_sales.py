from src.model.sale import Sales
from src.model.product import Produto
from typing import Optional


async def delete_or_update_product_sale(user_id: int, sale_code: str, product_id: int, new_quantity: Optional[int] = None):
    """
    Atualiza ou deleta um item da venda.

    - Se new_quantity for informado:
        - Atualiza a quantidade.
        - Recalcula total_price e lucro_total.
        - Ajusta o estoque do produto corretamente.
    - Se new_quantity for None:
        - Deleta a venda.
        - Devolve a quantidade total ao estoque do produto.
    """
    try:
        # Busca a venda
        sale = await Sales.filter(usuario_id=user_id, sale_code=sale_code, id=product_id).first()
        if not sale:
            return {"status": 404, "msg": "Nenhum registro encontrado para atualizar ou deletar."}

        # Busca o produto
        produto = await Produto.get(id=product_id)

        if new_quantity is not None:
            # Guarda quantidade antiga
            old_quantity = sale.quantity

            # Atualiza quantidade, total_price e lucro
            sale.quantity = new_quantity
            sale.total_price = new_quantity * produto.sale_price
            sale.lucro_total = new_quantity * (produto.sale_price - produto.cost_price)
            await sale.save()

            # Ajusta estoque corretamente
            produto.stock += (old_quantity - new_quantity)  # Se diminuiu, devolve para o estoque; se aumentou, diminui
            await produto.save()

            return {
                "status": 200,
                "msg": "Venda atualizada com sucesso!",
                "new_total_price": sale.total_price,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "new_stock": produto.stock
            }

        else:
            # Deleta venda e devolve quantidade ao estoque
            produto.stock += sale.quantity
            await produto.save()

            await sale.delete()
            return {"status": 200, "msg": "Venda deletada com sucesso.", "new_stock": produto.stock}

    except Exception as e:
        return {"status": 500, "error": f"Erro ao atualizar ou deletar venda: {str(e)}"}
