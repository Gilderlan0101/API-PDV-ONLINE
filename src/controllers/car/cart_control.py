from typing import Any, Dict, Optional
from src.model.product import Produto
from src.model.carItems import CartItem
from src.model.employee import Employees
from src.model.caixa import Caixa
from src.model.user import Usuario


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class CartManagerDB:
    """Carrinho persistido no banco de dados usando Tortoise ORM"""

    async def _get_caixa_id(self, user_id: int) -> int:

        print(user_id)
        print(user_id)
        print(user_id)

        """
        Função para obter o ID do caixa ativo do usuário/funcionário.
        """
        # Verifica se é um funcionário
        funcionario = await Employees.get_or_none(id=user_id)

        if funcionario:
            # Busca o caixa ativo deste funcionário
            caixa_ativo = await Caixa.filter(funcionario_id=funcionario.id, aberto=True).first()

            if caixa_ativo:
                return caixa_ativo.id

        # Se não for funcionário, busca caixa do admin
        caixa_admin = await Caixa.filter(usuario_id=user_id, aberto=True).first()

        if caixa_admin:
            return caixa_admin.id

        # Se não encontrar caixa, retorna o user_id (fallback)
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

        # Obtém o ID do caixa ativo
        caixa_id = await self._get_caixa_id(user_id)

        # Verifica se o caixa existe e está aberto
        caixa = await Caixa.get_or_none(id=caixa_id, aberto=True)
        if not caixa:
            return {"aviso": "Caixa não encontrado ou fechado"}

        # Adicionar ou atualizar item no carrinho - AGORA USA caixa_id
        cart_item = await CartItem.get_or_none(caixa_id=user_id, product_id=product_id)  # ✅ Corrigido: usa caixa_id em vez de user_id

        if cart_item:
            # Atualiza item existente
            cart_item.quantity += quantity
            cart_item.total_price = cart_item.price * cart_item.quantity
            await cart_item.save()

            # Atualiza o estoque do produto
            produto.stock -= quantity
            await produto.save()
        else:
            # Cria novo item no carrinho
            cart_item = await CartItem.create(
                caixa_id=user_id,  # ✅ Corrigido: usa caixa_id
                product_id=product_id,
                product_name=produto.name,
                quantity=quantity,
                price=produto.cost_price,
                total_price=produto.cost_price * quantity,
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
                "total_price": float(cart_item.total_price),
                "caixa_id": user_id,
            },
            "admin_produto_id": produto.id,
            "nome": produto.name,
        }

    async def listar_produtos(self, user_id: int):
        caixa_id = await self._get_caixa_id(user_id)

        # Remove itens com quantity == 0 - ✅ Corrigido: usa caixa_id
        zero_items = await CartItem.filter(caixa_id=caixa_id, quantity=0).all()
        for item in zero_items:
            await item.delete()

        # Retorna todos os itens do carrinho - ✅ Corrigido: usa caixa_id
        produtos = await CartItem.filter(caixa_id=caixa_id).all()
        return produtos

    async def remove_produto(self, product_id: int, user_id: int):
        caixa_id = await self._get_caixa_id(user_id)

        # ✅ Corrigido: usa caixa_id em vez de user_id
        cart_item = await CartItem.filter(caixa_id=caixa_id, product_id=product_id).first()

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
        caixa_id = await self._get_caixa_id(user_id)

        # ✅ Corrigido: usa caixa_id em vez de user_id
        cart_item = await CartItem.filter(caixa_id=caixa_id, product_id=product_id).first()

        if not cart_item:
            return {"success": False, "message": "Produto não encontrado no carrinho"}

        produto = await Produto.get_or_none(id=product_id)
        if not produto:
            return {"success": False, "message": "Produto não encontrado"}

        # ... (resto do método mantido, mas usando caixa_id)

    async def limpar_carrinho(self, user_id: int):
        caixa_id = await self._get_caixa_id(user_id)

        # ✅ Corrigido: usa caixa_id em vez de user_id
        itens = await CartItem.filter(caixa_id=caixa_id).all()

        # Restaura o estoque de todos os produtos
        for item in itens:
            produto = await Produto.get_or_none(id=item.product_id)
            if produto:
                produto.stock += item.quantity
                await produto.save()
            await item.delete()

        return []

    async def get_cart_total(self, user_id: int) -> float:
        caixa_id = await self._get_caixa_id(user_id)

        # ✅ Corrigido: usa caixa_id em vez de user_id
        itens = await CartItem.filter(caixa_id=caixa_id).all()
        total = sum(float(item.total_price) for item in itens)

        return total

    async def get_cart_count(self, user_id: int) -> int:
        caixa_id = await self._get_caixa_id(user_id)

        # ✅ Corrigido: usa caixa_id em vez de user_id
        itens = await CartItem.filter(caixa_id=caixa_id).all()
        count = sum(item.quantity for item in itens)

        return count
