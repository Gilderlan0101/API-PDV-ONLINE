from typing import Any, Dict, Optional
from src.model.product import Produto
from src.model.carItems import CartItem
from src.model.employee import Employees


# Função para formatar valores em Real brasileiro
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class CartManagerDB:
    """Carrinho persistido no banco de dados usando Tortoise ORM"""

    async def add_produto(
        self,
        product_id: int,
        quantity: int,
        user_id: int,
        # product_code: str,
    ) -> Dict[str, Any]:
        # Buscar o produto
        produto = await Produto.get_or_none(id=product_id)
        if not produto:
            return {"aviso": "Produto não encontrado"}
        if produto.stock < quantity:
            return {"aviso": "Estoque insuficiente"}

        # Verificar se o user_id é funcionário e pegar o admin dono
        funcionario = await Employees.get_or_none(id=user_id)
        if funcionario and funcionario.usuario:
            user_id_carrinho = funcionario.id  # carrinho do admin
            funcionario_id = funcionario.id
            funcionario_nome = funcionario.nome
        else:
            user_id_carrinho = user_id  # admin adicionando direto
            funcionario_id = None
            funcionario_nome = None

        # Adicionar ou atualizar item no carrinho
        cart_item = await CartItem.get_or_none(user_id=user_id_carrinho, product_id=product_id)
        if cart_item:
            cart_item.quantity += quantity
            cart_item.price_total += produto.sale_price * quantity
            # product_code = cart_item.product_code
            await cart_item.save()
        else:
            cart_item = await CartItem.create(
                user_id=user_id_carrinho,
                product_id=product_id,
                product_name=produto.name,
                quantity=quantity,
                price=produto.sale_price,
                total_price=produto.sale_price * quantity,
            )

        return {
            "item_adicionado": cart_item,
            "funcionario": {"id": funcionario_id, "nome": funcionario_nome},
            "admin_produto_id": produto.id,
            "nome": produto.name,
        }

    async def listar_produtos(self, user_id: int):
        # Remove itens com quantity == 0
        zero_items = await CartItem.filter(user_id=user_id, quantity=0).all()
        for item in zero_items:
            await item.delete()

        produtos = await CartItem.filter(user_id=user_id).all()
        return produtos

    async def remove_produto(self, product_id: int, user_id: int):
        cart_item = await CartItem.filter(user_id=user_id, product_id=product_id).first()
        if cart_item:
            await cart_item.delete()
        return {"aviso": "Produto removido"}

    async def update_produto(
        self,
        product_id: int,
        user_id: int,
        quantity: Optional[int] = None,
        discount: Optional[float] = None,
        addition: Optional[float] = None,
        replace_quantity: bool = False,
        replace_discount: bool = False,
        replace_addition: bool = False,
    ) -> Dict[str, Any]:
        cart_item = await CartItem.filter(user_id=user_id, product_id=product_id).first()
        if not cart_item:
            return {"aviso": "Produto não encontrado no carrinho"}

        # --- Quantidade ---
        if quantity is not None:
            cart_item.quantity = quantity if replace_quantity else (cart_item.quantity or 0) + quantity

        subtotal = cart_item.price * cart_item.quantity

        # --- Desconto ---
        if discount is not None:
            cart_item.discount = discount if replace_discount else (cart_item.discount or 0) + discount
        if cart_item.discount and cart_item.discount > subtotal:
            cart_item.discount = subtotal

        # --- Acréscimo ---
        if addition is not None:
            cart_item.addition = addition if replace_addition else (cart_item.addition or 0) + addition

        # --- Total ---
        cart_item.total_price = subtotal - (cart_item.discount or 0) + (cart_item.addition or 0)
        if cart_item.price_total < 0:
            cart_item.price_total = 0

        if cart_item.quantity == 0:
            await cart_item.delete()
            return {"aviso": f"{cart_item.product_name} removido do carrinho"}

        await cart_item.save()

        return {
            "produto": cart_item.product_name,
            "quantidade": cart_item.quantity,
            "preco_unitario": format_brl(cart_item.price),
            "desconto": format_brl(cart_item.discount or 0),
            "acrescimo": format_brl(cart_item.addition or 0),
            "total": format_brl(cart_item.price_total),
        }

    async def limpar_carrinho(self, user_id: int):
        itens = await CartItem.filter(user_id=user_id).all()
        for item in itens:
            await item.delete()
        return []
