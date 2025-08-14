import asyncio
from src.controllers.car.cart_control import CartManagerDB


async def main():
    cart = CartManagerDB()
    user_id = 1  # ID do usuário para teste

    # Adicionando produtos
    resp1 = await cart.add_produto(product_id=1, quantity=2, user_id=user_id)
    print(resp1)

    resp2 = await cart.add_produto(product_id=2, quantity=3, user_id=user_id)
    print(resp2)

    # Adicionando mais quantidade do mesmo produto
    resp3 = await cart.add_produto(product_id=1, quantity=1, user_id=user_id)
    print(resp3)

    # Listando produtos no carrinho
    itens = await cart.listar_produtos(user_id)
    print("Carrinho atual:", itens)

    # Limpando carrinho
    resp4 = await cart.limpar_carrinho(user_id)
    print(resp4)


asyncio.run(main())
