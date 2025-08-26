import locale
from typing import Any, Dict, Optional
from sqlmodel import Session, select, delete
from src.model.product import Produto
from src.model.carItems import CartItem
from src.conf.database import engine



# Configura locale para Real brasileiro
locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

class CartManagerDB:
    """Carrinho persistido no banco de dados"""

    async def add_produto(
        self,
        product_id: int,
        quantity: int,
        user_id: int,
        sale_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Adiciona um produto ao carrinho.

        Args:
            product_id (int): ID do produto a ser adicionado.
            quantity (int): Quantidade do produto.
            user_id (int): ID do usuário dono do carrinho.
            sale_code (Optional[str]): Código da venda, se aplicável.

        Returns:
            dict: Informações do item adicionado ou mensagem de aviso.
        """
        with Session(engine) as session:
            produto = session.get(Produto, product_id)
            if not produto:
                return {"aviso": "Produto não encontrado"}
            if produto.stock < quantity:
                return {"aviso": "Estoque insuficiente"}

            cart_item = session.exec(
                select(CartItem).where(
                    CartItem.user_id == user_id, CartItem.product_id == product_id
                )
            ).first()

            if cart_item:
                cart_item.quantity += quantity
                cart_item.total_price += produto.sale_price * quantity
                cart_item.sale_code = sale_code
            else:
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    product_name=produto.name,
                    quantity=quantity,
                    price=produto.sale_price,
                    total_price=produto.sale_price * quantity,
                    sale_code=sale_code,
                )
                session.add(cart_item)
            session.commit()
            session.refresh(cart_item)
            return {"item_adicionado": cart_item}

    async def remove_produto(self, product_id: int, user_id: int):
        with Session(engine) as session:
            stmt = delete(CartItem).where(
                (CartItem.user_id == user_id) & (CartItem.product_id == product_id)  # type: ignore
            )
            session.exec(stmt)  # type: ignore
            session.commit()
            return {"aviso": "Produto removido"}

    async def listar_produtos(self, user_id: int):
        with Session(engine) as session:
            # Remover itens com quantity == 0
            stmt = delete(CartItem).where(CartItem.user_id == user_id, CartItem.quantity == 0) # type: ignore
            session.exec(stmt)  # type: ignore
            session.commit()

            # Buscar produtos restantes no carrinho
            produtos = session.exec(
                select(CartItem).where(CartItem.user_id == user_id)
            ).all()

        return produtos
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
        with Session(engine) as session:
            cart_item = session.exec(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            )
        ).first()

        if not cart_item:
            return {"aviso": "Produto não encontrado no carrinho"}

        # --- Quantidade ---
        if quantity is not None:
            if replace_quantity:
                cart_item.quantity = max(0, quantity)
            else:
                cart_item.quantity = max(0, (cart_item.quantity or 0) + quantity)

        # Subtotal (sem desconto/acréscimo)
        subtotal = cart_item.price * cart_item.quantity

        # --- Desconto ---
        if discount is not None:
            if replace_discount:
                cart_item.discount = max(0, discount)  # substitui
            else:
                cart_item.discount = max(0, (cart_item.discount or 0) + discount)  # acumula

        # 🔒 Garantir que desconto nunca ultrapasse subtotal
        if cart_item.discount and cart_item.discount > subtotal:
            cart_item.discount = subtotal

        # --- Acréscimo ---
        if addition is not None:
            if replace_addition:
                cart_item.addition = max(0, addition)
            else:
                cart_item.addition = max(0, (cart_item.addition or 0) + addition)

        # --- Recalcular total ---
        cart_item.total_price = subtotal - (cart_item.discount or 0) + (cart_item.addition or 0)

        # 🔒 Evitar negativo
        if cart_item.total_price < 0:
            cart_item.total_price = 0

        # Se quantidade zerar → remover item
        if cart_item.quantity == 0:
            session.delete(cart_item)
            session.commit()
            return {"aviso": f"{cart_item.product_name} removido do carrinho"}

        session.add(cart_item)
        session.commit()
        session.refresh(cart_item)

        return {
            "produto": cart_item.product_name,
            "quantidade": cart_item.quantity,
            "preco_unitario": locale.currency(cart_item.price, grouping=True),
            "desconto": locale.currency(cart_item.discount or 0, grouping=True),
            "acrescimo": locale.currency(cart_item.addition or 0, grouping=True),
            "total": locale.currency(cart_item.total_price, grouping=True),
        }
