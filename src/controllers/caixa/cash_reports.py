from fastapi import HTTPException
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import Optional
from src.model.caixa import Caixa
from src.model.sale import Sales
from src.model.user import Usuario
from src.model.cashmovement import CashMovement
from src.model.employee import Employees
from src.utils.status_code import *
from src.utils.payments_config import *

# Cahe Redis
from src.core.cache import client
import json

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from tortoise.expressions import Q


class CashReportController:
    # 🔹 Cache de classe: Armazena dados já carregados

    async def get_cash_reports(self, user_id: int, filter_data: Optional[datetime] = None, employee_name: Optional[str] = None) -> list[dict]:
        """
        Busca e retorna relatórios de caixa com cache.
        """

        # Define a data padrão se nenhuma for fornecida
        current_date_tz = datetime.now(ZoneInfo('America/Sao_Paulo'))

        # 🔹 Lógica da Cache
        # Chave da cache: Combina a data e o nome do funcionário para unicidade
        cache_key = f"cash_reports:{filter_data}" or f"cash_reports:{employee_name}"
        cache = await client.get(cache_key)

        # 🔹 Tenta retornar do cache se a chave existir
        if cache:
            print(f"✅ Retornando dados do cache para a chave: {cache}")
            return json.loads(cache)

        current_user = await Usuario.get_or_none(id=user_id)
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Usuario não encontrado.')

        # 🔹 NOVO: Lógica para filtrar por nome do funcionário
        if employee_name:
            # Busca o funcionário pelo nome (busca case-insensitive)
            employee_query = await Employees.filter(Q(nome__icontains=employee_name)).first()
            if not employee_query:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Funcionário com o nome '{employee_name}' não encontrado.")

            # 🔹 Usa o ID do funcionário para o filtro
            cash_movement_query = CashMovement.filter(Q(funcionario_id=employee_query.id) & Q(usuario_id=user_id))
        else:
            # Busca todos os movimentos do usuário se nenhum nome for fornecido
            cash_movement_query = CashMovement.filter(usuario_id=user_id)

        # 🔹 Filtra pela data fornecida, se existir
        if filter_data:
            cash_movement_query = cash_movement_query.filter(criado_em__date=filter_data.date())

        cash_movements = await cash_movement_query.order_by("-criado_em")

        if not cash_movements:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Nenhum movimento de caixa encontrado com os filtros aplicados.')

        movement_data = []
        result_valor = 0.0
        for moviment in cash_movements:
            print(moviment.valor)
            print(moviment.valor)
            print(type(moviment.valor))
            print(type(moviment.valor))
            tipo_movimento = moviment.tipo
            result_valor += float(moviment.valor)
            movement_data.append(
                {
                    "Abertura": moviment.criado_em.strftime('%d/%m/%Y %H:%M'),
                    "Tipo_movimento": tipo_movimento,
                    "Valor_entrada": float(moviment.valor),
                    "caixa": moviment.caixa_id,
                    "Resultado": f"{result_valor:,.2f}",
                }
            )

        await client.setex(cache_key, 60, json.dumps(movement_data))
        return movement_data
