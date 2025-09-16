from typing import Any, Dict, Optional
from src.model.product import Produto
from src.model.carItems import CartItem
from src.model.employee import Employees
from src.model.user import Usuario

# Função para formatar valores em Real brasileiro
def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class CartManagerDB:
    """Carrinho persistido no banco de dados usando Tortoise ORM"""

    async def _get_cart_owner_id(self, user_id: int) -> int:
        """
        Função auxiliar para obter o ID do dono do carrinho.
        Se o usuário logado for um funcionário, o carrinho pertence ao seu administrador.
        Se for o administrador, o carrinho pertence a ele mesmo.
        """
        # Verifica se o user_id existe na tabela de funcionários
        funcionario = await Employees.get_or_none(id=user_id)
        
        if funcionario:
            # Se for funcionário, retorna o ID do admin (usuario_id)
            return funcionario.usuario_id
        
        # Se não for funcionário, retorna o próprio ID (admin)
        return user_id

    async def add_produto(
        self,
        product_id: int,
        quantity: int,
        user_id: int,
    ) -> Dict[str, Any]:
        produto = await Produto.get_or_none(id=product_id)
        if not produto:
            return {"aviso": "Produto não encontrado"}
        
        if produto.stock < quantity:
            return {"aviso": "Estoque insuficiente"}

        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        # Adicionar ou atualizar item no carrinho
        cart_item = await CartItem.get_or_none(
            user_id=user_id_carrinho, 
            product_id=product_id
        )
        
        if cart_item:
            # Atualiza item existente
            cart_item.quantity += quantity
            cart_item.price_total = cart_item.price * cart_item.quantity
            await cart_item.save()
            
            # Atualiza o estoque do produto
            produto.stock -= quantity
            await produto.save()
        else:
            # Cria novo item no carrinho
            cart_item = await CartItem.create(
                user_id=user_id_carrinho,
                product_id=product_id,
                product_name=produto.name,
                quantity=quantity,
                price=produto.total_price,
                total_price=produto.total_price * quantity,
            )
            
            # Atualiza o estoque do produto
            produto.stock -= quantity
            await produto.save()

        return {
            "success": True,
            "item_adicionado": {
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "product_name": cart_item.product_name,
                "quantity": cart_item.quantity,
                "price": float(cart_item.price),
                "total_price": float(cart_item.price_total)
            },
            "admin_produto_id": produto.id,
            "nome": produto.name,
        }

    async def listar_produtos(self, user_id: int):
        # Remove itens com quantity == 0
        zero_items = await CartItem.filter(user_id=user_id, quantity=0).all()
        for item in zero_items:
            await item.delete()

        # Retorna todos os itens do carrinho
        produtos = await CartItem.filter(user_id=user_id).all()
        return produtos

    async def remove_produto(self, product_id: int, user_id: int):
        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        cart_item = await CartItem.filter(
            user_id=user_id_carrinho, 
            product_id=product_id
        ).first()
        
        if cart_item:
            # Restaura o estoque do produto antes de remover
            produto = await Produto.get_or_none(id=product_id)
            if produto:
                produto.stock += cart_item.quantity
                await produto.save()
            
            await cart_item.delete()
            return {"success": True, "aviso": "Produto removido"}
        
        return {"success": False, "aviso": "Produto não encontrado no carrinho"}

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
        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        cart_item = await CartItem.filter(
            user_id=user_id_carrinho, 
            product_id=product_id
        ).first()
        
        if not cart_item:
            return {"success": False, "message": "Produto não encontrado no carrinho"}

        produto = await Produto.get_or_none(id=product_id)
        if not produto:
            return {"success": False, "message": "Produto não encontrado"}

        # Guarda a quantidade antiga para ajuste de estoque
        old_quantity = cart_item.quantity

        # --- Quantidade ---
        if quantity is not None:
            if replace_quantity:
                # Substitui a quantidade
                new_quantity = quantity
            else:
                # Adiciona à quantidade existente
                new_quantity = cart_item.quantity + quantity
            
            # Verifica se há estoque suficiente
            if new_quantity > old_quantity:
                quantidade_a_adicionar = new_quantity - old_quantity
                if produto.stock < quantidade_a_adicionar:
                    return {"success": False, "message": "Estoque insuficiente"}
            
            cart_item.quantity = new_quantity
        
        subtotal = cart_item.price * cart_item.quantity

        # --- Desconto ---
        if discount is not None:
            if replace_discount:
                cart_item.discount = discount
            else:
                cart_item.discount = (cart_item.discount or 0) + discount
            
            if cart_item.discount and cart_item.discount > subtotal:
                cart_item.discount = subtotal

        # --- Acréscimo ---
        if addition is not None:
            if replace_addition:
                cart_item.addition = addition
            else:
                cart_item.addition = (cart_item.addition or 0) + addition

        # --- Total ---
        cart_item.total_price = (
            (cart_item.price * cart_item.quantity) 
            - (cart_item.discount or 0) 
            + (cart_item.addition or 0)
        )
        
        if cart_item.total_price < 0:
            cart_item.total_price = 0

        # Atualiza o estoque do produto
        if quantity is not None:
            diferenca_quantidade = cart_item.quantity - old_quantity
            produto.stock -= diferenca_quantidade
            await produto.save()

        if cart_item.quantity == 0:
            await cart_item.delete()
            return {"success": True, "aviso": f"{cart_item.product_name} removido do carrinho"}

        await cart_item.save()

        return {
            "success": True,
            "produto": cart_item.product_name,
            "quantidade": cart_item.quantity,
            "preco_unitario": format_brl(cart_item.price),
            "desconto": format_brl(cart_item.discount or 0),
            "acrescimo": format_brl(cart_item.addition or 0),
            "total": format_brl(cart_item.total_price),
        }

    async def limpar_carrinho(self, user_id: int):
        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        itens = await CartItem.filter(user_id=user_id_carrinho).all()
        
        # Restaura o estoque de todos os produtos
        for item in itens:
            produto = await Produto.get_or_none(id=item.product_id)
            if produto:
                produto.stock += item.quantity
                await produto.save()
            await item.delete()
        
        return []

    async def get_cart_total(self, user_id: int) -> float:
        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        itens = await CartItem.filter(user_id=user_id_carrinho).all()
        total = sum(float(item.total_price) for item in itens)
        
        return total

    async def get_cart_count(self, user_id: int) -> int:
        user_id_carrinho = await self._get_cart_owner_id(user_id)
        
        itens = await CartItem.filter(user_id=user_id_carrinho).all()
        count = sum(item.quantity for item in itens)
        
        return count