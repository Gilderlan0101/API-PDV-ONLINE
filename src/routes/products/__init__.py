from fastapi import APIRouter

from .create import router as create_router
from .update import router as update_router
from .delete import router as delete_router
from .list import router as list_router
from .sales import router as sales_router

products_router = APIRouter(prefix='/produtos', tags=['Produtos'])

products_router.include_router(create_router, prefix='/create')
products_router.include_router(update_router, prefix='/update')
products_router.include_router(delete_router, prefix='/delete')
products_router.include_router(list_router, prefix='/list')
products_router.include_router(sales_router, prefix='/sales')
