from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.model.sale import Sales
from src.model.user import Usuario
from src.auth.deps import get_current_user

allDatas = APIRouter()


@allDatas.get('/profit')
async def profit(current_user: Usuario = Depends(get_current_user)):
    """Rota que exibe o lucro do dia em tempo real"""
    if not current_user.id:
        raise HTTPException(status_code=400, detail='Usuário inválido')

    try:
        # Data atual
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()

        # Define início e fim do dia
        start_of_day = datetime.combine(today, time.min, tzinfo=ZoneInfo("America/Sao_Paulo"))
        end_of_day = datetime.combine(today, time.max, tzinfo=ZoneInfo("America/Sao_Paulo"))

        # Busca todas as vendas do usuário no dia atual
        sales = await Sales.filter(
            usuario_id=current_user.id,
            criado_em__gte=start_of_day,
            criado_em__lte=end_of_day
        ).all()

        total_user_profit = 0.0  # Receita bruta total
        total_lucro = 0.0  # Lucro líquido total
        sales_of_the_day = len(sales)

        sales_list = []
        for sale in sales:
            total_user_profit += sale.total_price
            total_lucro += sale.lucro_total

            sales_list.append({
                'id': sale.id,
                'product_name': sale.product_name,
                'quantity': sale.quantity,
                'total_price': sale.total_price,
                'lucro_total': sale.lucro_total,
                'cost_price': sale.cost_price,
                'codigo_da_venda': sale.sale_code,
                'created_at': sale.criado_em.strftime('%d/%m/%Y %H:%M:%S') if sale.criado_em else None
            })

        return {
            'total_user_profit': f'{total_user_profit:.2f}',  # Receita bruta
            'total_lucro': f'{total_lucro:.2f}',  # Lucro líquido real
            'sales_of_the_day': sales_of_the_day,
            'sales': sales_list,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
