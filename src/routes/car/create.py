from fastapi import APIRouter, Depends, Query
from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.model.employee import Employees

from src.controllers.car.cart_control import CartManagerDB

router = APIRouter(tags=["Carrinho"])
cart = CartManagerDB()

@router.post("/adicionar")
async def adicionar_produto(
    product_id: int = Query(..., description="ID do produto a ser adicionado"),
    quantity: int = Query(..., gt=0, description="Quantidade do produto"),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Adiciona um produto ao carrinho do usuário ou funcionário.
    """
    # Verifica se o usuário atual é um funcionário
    funcionario = await Employees.filter(id=current_user.id).first()
    
    if funcionario:
        # Se for funcionário, usa o usuario_id do funcionário (que é o ID do admin)
        user_id_carrinho = funcionario.usuario_id
        print('E um fucionario')
    else:
        # Se não for funcionário, é admin e usa seu próprio ID
        user_id_carrinho = current_user.id
        print('Não e um fucionario')
    
    return await cart.add_produto(product_id, quantity, user_id_carrinho)