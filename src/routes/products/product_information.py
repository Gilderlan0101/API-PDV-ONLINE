
from fastapi import APIRouter, Depends
from src.routes.products.list import list_products
from src.auth.deps import get_current_user
from src.schemas.schema_user import SystemUser
from src.controllers.products.monitoring_products import ProductsInfos


@list_products.get('/por_categoria')
async def products_by_category(current_user: SystemUser = Depends(get_current_user)):

	var = ProductsInfos(current_user.id)
	await var.Quantity_products_stoke()
	teste = await var.separating_products_by_category()
	return teste



@list_products.get('/quantidade_stoke')
async def Quantity_prod_stoke(current_user: SystemUser = Depends(get_current_user)):

	var = ProductsInfos(current_user.id)
	
	return await var.Quantity_products_stoke()


@list_products.get('/valor_stoke')
async def price_of_all_stock_(current_user: SystemUser = Depends(get_current_user)):

	var = ProductsInfos(current_user.id)
	
	return await var.price_of_all_stock()