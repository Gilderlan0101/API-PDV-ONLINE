from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, time
from zoneinfo import ZoneInfo
from tortoise.functions import Sum  # Import necessário para agregar
from src.model.sale import Sales
from src.model.user import Usuario
from src.auth.deps import get_current_user, SystemUser
from src.utils.sales_of_the_day import sales_of_the_day, total_in_sales
from typing import Dict, Any, List

allDatas = APIRouter()


@allDatas.get('/profit')
async def profit(current_user: SystemUser = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Rota que exibe métricas de vendas e lucro do dia (dashboard).
    """
    if not current_user.empresa_id:
        raise HTTPException(status_code=400, detail='Usuário inválido')

    try:
        # --- 1. DEFINIÇÃO DE DATAS ---
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        start_of_day = datetime.combine(today, time.min, tzinfo=ZoneInfo("America/Sao_Paulo"))
        end_of_day = datetime.combine(today, time.max, tzinfo=ZoneInfo("America/Sao_Paulo"))

        # --- 2. CONSULTAS ---

        # A. Busca todas as vendas do usuário no dia atual (para iteração e lista)
        sales_of_the_day_list = await Sales.filter(
            usuario_id=current_user.empresa_id,
            criado_em__gte=start_of_day,
            criado_em__lte=end_of_day,
        ).all()

        # B. Consulta de Agregação (para total de itens vendidos no dia)
        daily_aggregation = (
            await Sales.filter(
                usuario_id=current_user.empresa_id,
                criado_em__gte=start_of_day,
                criado_em__lte=end_of_day,
            )
            .annotate(total_items_sold=Sum('quantity'))
            .first()
        )

        # C. Contagem de Vendas Únicas (usando a função corrigida)
        qtd_sales_day = await sales_of_the_day(current_user.empresa_id)

        # A única informação que é persistida no banco de dados,
        # não sendo recalculada ou zerada automaticamente pelo sistema ou rotinas diárias.
        __valor__no__update__ = await total_in_sales(current_user.empresa_id)

        # D. Contagem de Vendas (Histórico Total)
        total_sales_count = await Sales.filter(usuario_id=current_user.empresa_id).count()

        # --- 3. PROCESSAMENTO DE DADOS ---
        total_user_profit = 0.0  # Receita bruta total do dia
        total_lucro = 0.0  # Lucro líquido total do dia
        sales_list: List[Dict] = []

        for sale in sales_of_the_day_list:
            total_user_profit += sale.total_price
            total_lucro += sale.lucro_total

            sales_list.append(
                {
                    'id': sale.id,
                    'product_name': sale.product_name,
                    'quantity': sale.quantity,
                    'total_price': sale.total_price,
                    'lucro_total': sale.lucro_total,
                    'cost_price': sale.cost_price,
                    'codigo_da_venda': sale.sale_code,
                    'created_at': (sale.criado_em.strftime('%d/%m/%Y %H:%M:%S') if sale.criado_em else None),
                }
            )

        # Total de itens vendidos hoje
        total_items_sold_today = daily_aggregation.total_items_sold if daily_aggregation and daily_aggregation.total_items_sold is not None else 0

        # --- 4. RETORNO OTIMIZADO ---
        return {
            # 🎯 MÉTRICAS DO DIA
            'total_user_profit': f'{total_user_profit:.2f}',  # Receita bruta do dia
            'total_lucro': f'{__valor__no__update__:.2f}',  # Lucro líquido real
            'sales_of_the_day': qtd_sales_day,  # Quantidade de Vendas Únicas (Transações) do dia
            'total_items_sold_today': total_items_sold_today,  # Quantidade total de itens vendidos hoje
            # 🎯 MÉTRICAS GERAIS
            'total_sales_count_history': total_sales_count,  # Quantidade TOTAL de registros de vendas (linhas na tabela)
            # 🎯 DADOS DETALHADOS
            'sales': sales_list,  # Lista de todas as vendas do dia
            # Codigo de venda
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar dados de lucro: {str(error)}")
