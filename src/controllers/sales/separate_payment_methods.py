from fastapi import HTTPException, status
from src.model.sale import Sales


async def separating_sales_by_payments(user_id: int) -> dict[list]:
    """
    Separa todas as vendas por métodos de pagamentos.
    methods: (dict): Pix, Cartão, Dinheiro, Nota, Fiado.
    """
    methods = {'Pix': [], 'Cartão': [], 'Dinheiro': [], 'Nota': [], 'Fiado': []}

    try:
        if not user_id:
            return methods

        all_sales = await Sales.filter(usuario_id=user_id)

        for prod in all_sales:
            data = {
                'Product_name': prod.product_name,
                'amount': prod.quantity,
                'date': prod.criado_em.date().strftime("%d/%m/%Y, %H:%M"),
            }

            payment = prod.payment_method.capitalize()
            if payment in methods:
                methods[payment].append(data)
            else:
                methods[payment] = [data]

        return methods

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detailf=f'Erro desconhecido: {e}')
