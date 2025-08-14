from fastapi import APIRouter

from .create import router as create_router
from .update import router as update_router
from .delete import router as delete_router
from .list import router as list_router
from .sales import router as sales_router
from .cancel_sale import router as cancel

products_router = APIRouter(
    prefix="/sales",
    tags=["Vendas"],
    responses={404: {"description": "Não encontrado"}},)

products_router.include_router(create_router, prefix='/create')
products_router.include_router(update_router, prefix='/update')
products_router.include_router(delete_router, prefix='/delete')
products_router.include_router(list_router, prefix='/list')
products_router.include_router(sales_router, prefix='/sales')
products_router.include_router(cancel)

