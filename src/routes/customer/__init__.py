from fastapi import APIRouter
from .customer_registration import customers as route


customers = APIRouter(
    responses={404: {"description": "Não encontrado"}},
)


customers.include_router(route)