from fastapi import APIRouter, Depends, HTTPException
from src.model.user.users import Usuario, Sales
from src.auth.deps import get_current_user
from src.conf.database import engine
from sqlmodel import Session,  select

class AllDatas:
    def __init__(self) -> None:
        self.allDatas = APIRouter()
        
        
        self.statup_route()

    def statup_route(self):
        """
        Essas rotas fornecem os dados essenciais para exibição na home da dashboard,
        incluindo: ganhos totais, produtos mais vendidos, horários de pico de venda,
        caixas com maior volume de vendas, entre outros insights relevantes.
        """
        
        @self.allDatas.get('/profit')
        async def profit(current_user: Usuario = Depends(get_current_user)):
            """Rota que exibe o lucro do dia em tempo real"""
            total_user_profit = 0.0
            total = 0.0
            sales_of_the_day = 0
            
            

            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            try:
                with Session(engine) as session:
                    # Busca todas as vendas do usuário
                    sales = session.exec(
                        select(Sales).where(Sales.usuario_id == current_user.id)
                    ).all()

                    total_user_profit = 0.0  # Receita bruta total (soma total_price)
                    total = 0.0              # Lucro líquido total (total_price - custo)
                    sales_of_the_day = 0     # Contador de vendas

                    for sale in sales:
                        total_user_profit += sale.total_price
                        total += sale.lucro_total  # lucro_total deve ser lucro líquido (total_price - custo)
                        sales_of_the_day += 1

                return {
                    'total_user_profit': f'{total_user_profit:.2f}',  # Receita bruta
                    'total': f'{total:.2f}',                          # Lucro líquido real
                    'sales_of_the_day': sales_of_the_day,
                    'sales': sales
                }

            except Exception as error:
                raise HTTPException(status_code=500, detail=str(error))

