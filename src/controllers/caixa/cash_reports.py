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


from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
from tortoise.expressions import Q


class CashReportController:
    # 🔹 Cache de classe: Armazena dados já carregados
    _cached_reports = {}

    async def get_cash_reports(self, user_id: int, filter_data: Optional[datetime] = None, employee_name: Optional[str] = None) -> list[dict]:
        """
        Busca e retorna relatórios de caixa com cache.
        """

        # Define a data padrão se nenhuma for fornecida
        current_date_tz = datetime.now(ZoneInfo('America/Sao_Paulo'))

        # 🔹 Lógica da Cache
        # Chave da cache: Combina a data e o nome do funcionário para unicidade
        cache_key = (
            ('default', employee_name.strip().upper() if employee_name else '')
            if not filter_data
            else (filter_data.strftime('%Y-%m-%d'), employee_name.strip().upper() if employee_name else '')
        )

        # 🔹 Tenta retornar do cache se a chave existir
        if cache_key in self._cached_reports:
            print(f"✅ Retornando dados do cache para a chave: {cache_key}")
            return self._cached_reports[cache_key]

        # 🔹 Se não estiver na cache, faz a busca no banco de dados
        print(f"❌ Cache não encontrada. Buscando dados no banco...")

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

        # 🔹 CORREÇÃO: Filtra pela data fornecida, se existir
        if filter_data:
            cash_movement_query = cash_movement_query.filter(criado_em__date=filter_data.date())

        cash_movements = await cash_movement_query.order_by("-criado_em")

        if not cash_movements:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Nenhum movimento de caixa encontrado com os filtros aplicados.')

        movement_data = []
        result_valor = 0
        for moviment in cash_movements:
            tipo_movimento = moviment.tipo
            result_valor += moviment.valor
            movement_data.append(
                {
                    "Abertura": moviment.criado_em.strftime('%d/%m/%Y %H:%M'),
                    "Tipo_movimento": tipo_movimento,
                    "Valor_entrada": round(moviment.valor, 2),
                    "caixa": moviment.caixa_id,
                    "Resultado": result_valor,
                }
            )

        self._cached_reports[cache_key] = movement_data

        # Lógica para popular a cache padrão
        if filter_data and ('default', '') not in self._cached_reports:
            default_query = await CashMovement.filter(usuario_id=user_id).order_by("-criado_em")
            default_data = [
                {
                    "Abertura": m.criado_em.date().strftime('%d/%m/%Y'),
                    "Tipo_movimento": m.tipo,
                    "Valor_entrada": round(m.valor, 2),
                    "Descricao": m.descricao if m.descricao == "FECHAMENTO" else 'ABERTO',
                    "caixa": m.caixa_id,
                }
                for m in default_query
            ]
            self._cached_reports[('default', '')] = default_data

        return movement_data
