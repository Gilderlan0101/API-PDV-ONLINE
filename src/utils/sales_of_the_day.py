from src.model.sale import Sales


async def sales_of_the_day(user_id: int) -> int:
    """sales_of_the_day: Retorna a quantidade de vendas concluidas"""

    try:
        # Quantidade de vendas
        sales_quantity = 0

        # Buscando vendas do usuario
        sales = await Sales.filter(usuario_id=user_id).all()

        # Lista onde vamos amazerna os codegidos das vendas | sale_code
        codes = [sale.sale_code for sale in sales]

        sales_quantity = len(set(codes))  # Pegando valores unicos
        # Retonando quantidade de vendas
        return sales_quantity

    except Exception as e:
        print(e)
        return 0
