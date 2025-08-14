from typing import Any, Dict, Optional
from sqlmodel import Session, select, delete
from src.model.product import Produto
from src.model.carItems import CartItem
from src.conf.database import engine


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

    async def limpar_carrinho(self, user_id: int):
        with Session(engine) as session:
            stmt = delete(CartItem).where(CartItem.user_id == user_id)  # type: ignore
            session.exec(stmt)  # type: ignore
            session.commit()
            return {"aviso": "Carrinho limpo"}

    async def listar_produtos(self, user_id: int):
        with Session(engine) as session:
            return session.exec(
                select(CartItem).where(CartItem.user_id == user_id)
            ).all()

    async def remover_produtos_por_venda(self, sale_code: str) -> Dict[str, Any]:
        """
        Remove produtos do carrinho que já foram vendidos, baseado no código da venda.

        Args:
            sale_code (str): Código da venda a ser removida.

        Returns:
            dict: Aviso sobre quantos produtos foram removidos.
        """
        with Session(engine) as session:
            items = session.exec(
                select(CartItem).where(CartItem.sale_code == sale_code)
            ).all()

            if not items:
                return {"aviso": "Nenhum produto encontrado para este código de venda."}

            for item in items:
                session.delete(item)
            session.commit()
            return {"aviso": f"{len(items)} produtos removidos do carrinho."}
