import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from src.controllers.caixa.cash_reports import CashReportController
from src.auth.deps import get_current_user, SystemUser


logger = logging.getLogger(__name__)
router = APIRouter()
cash_report_controller = CashReportController()


@router.get("/relatorio_caixa")
async def get_cash_report_route(
    current_user: SystemUser = Depends(get_current_user),
    filter_data: Optional[datetime] = Query(None),
    employee_name: Optional[str] = Query(None),
):
    """Gera relatório de caixa"""

    logger.info("Gerando relatório de caixa", extra={"user_id": current_user.id, "filter_data": filter_data, "employee_name": employee_name})

    reports = await cash_report_controller.get_cash_reports(user_id=current_user.id, filter_data=filter_data, employee_name=employee_name)

    logger.debug(
        "Relatório de caixa gerado", extra={"user_id": current_user.id, "total_relatorios": len(reports) if isinstance(reports, list) else 1}
    )

    return reports
