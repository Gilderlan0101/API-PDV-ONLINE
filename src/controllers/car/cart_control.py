from typing import Any, Dict, List
from fastapi import HTTPException, status
from src.model.product import Produto
from src.model.carItems import CartItem
from src.model.caixa import Caixa


class CartManagerDB:
    """
    Gerencia o carrinho de um funcionário dentro de um caixa ativo.
    Implementa controle multi-tenant (empresa + funcionário).
    """

    def __init__(self, company_id: int, employee_id: int):
        self.company_id = company_id  # ID da empresa (usuario_id)
        self.employee_id = employee_id  # ID do funcionário (funcionario_id)

    async def _get_caixa_ativo(self) -> Caixa:
        """
        Busca o caixa ativo vinculado ao funcionário e à empresa.
        """
        try:
            # 🎯 Busca usando as duas chaves: usuario_id (empresa) e funcionario_id
            caixa = await Caixa.filter(usuario_id=self.company_id, funcionario_id=self.employee_id, aberto=True).first()

            if not caixa:
                # 🛑 Erro 400 se o caixa não estiver aberto.
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum caixa aberto encontrado para este funcionário/empresa.")

            return caixa

        except HTTPException:
            raise
        except Exception as e:
            # 🛑 Erro 500 para falhas inesperadas de banco
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar caixa: {str(e)}")

    async def add_produto(self, product_id: int, quantity: int, empresa_id: int, employee_id: int) -> Dict[str, Any]:
        """
        Adiciona um produto ao carrinho (caixa ativo do funcionário).
        """
        caixa = await self._get_caixa_ativo()

        # Busca produto pertencente à empresa
        produto = await Produto.get_or_none(id=product_id, usuario_id=empresa_id)

        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado nesta empresa.")

        if produto.stock < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente.")

        # 🎯 CORREÇÃO: Usar .filter().first() em vez de .get_or_none() para evitar MultipleObjectsReturned
        cart_item = await CartItem.filter(caixa_id=caixa.caixa_id, product_id=product_id).first()

        if cart_item:
            # Se o item existe, delega a lógica de estoque e atualização para update_produto
            return await self.update_produto(product_id, int(cart_item.quantity) + int(quantity), empresa_id)

        # Cria item de carrinho
        cart_item = await CartItem.create(
            caixa_id=caixa.caixa_id,
            product_id=product_id,
            product_name=produto.name,
            quantity=quantity,
            price=produto.sale_price,
            total_price=produto.sale_price * quantity,
            product_code=produto.product_code,
        )

        # Atualiza estoque do produto (subtrai)
        produto.stock -= quantity
        await produto.save()

        return {
            "success": True,
            "item_adicionado": {
                "id": product_id,
                "product_id": cart_item.product_id,
                "product_name": cart_item.product_name,
                "quantity": cart_item.quantity,
                "price": float(cart_item.price),
                "total_price": float(cart_item.total_price),
                "caixa_id": caixa.caixa_id,
                "empresa_id": empresa_id,
                "employee_id": employee_id,
            },
        }

        
    async def update_produto(self, product_id: int, new_quantity: int, empresa_id: int) -> Dict[str, Any]:
        """
        Atualiza a quantidade de um item no carrinho e ajusta o estoque.
        """
        caixa = await self._get_caixa_ativo()

        # 🎯 CORREÇÃO: Usar .filter().first() em vez de .get_or_none() para evitar MultipleObjectsReturned
        cart_item = await CartItem.filter(caixa_id=caixa.caixa_id, product_id=product_id).first()
        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado no carrinho.")

        produto = await Produto.get_or_none(id=product_id, usuario_id=empresa_id)
        if not produto:
            # Caso o produto tenha sido deletado do inventário, apenas atualiza o carrinho (sem ajuste de estoque).
            pass

        old_quantity = cart_item.quantity
        quantity_difference = int(new_quantity) - int(old_quantity)

        if new_quantity <= 0:
            # Se a nova quantidade for zero ou menor, remove o item
            if produto:
                produto.stock += old_quantity  # Restaura o estoque antigo
                await produto.save()
            await cart_item.delete()
            return {"success": True, "aviso": "Produto removido do carrinho por quantidade zero."}

        if produto:
            # Verifica o estoque para aumentos
            if quantity_difference > 0 and produto.stock < quantity_difference:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente para aumentar a quantidade.")

            # Ajusta o estoque: subtrai se aumentou, adiciona se diminuiu
            produto.stock -= quantity_difference
            await produto.save()

        # Atualiza o item do carrinho
        cart_item.quantity = new_quantity
        cart_item.total_price = cart_item.price * new_quantity
        await cart_item.save()

        return {
            "success": True,
            "item_atualizado": {
                "id": product_id,
                "product_name": cart_item.product_name,
                "quantity": cart_item.quantity,
                "total_price": float(cart_item.total_price),
            },
        }

    async def listar_produtos(self, empresa_id: int, employee_id: int) -> List[Dict[str, Any]]:
        """
        Lista os produtos ATUALMENTE NO CARRINHO (itens do caixa ativo).
        Esta rota NÃO lista o inventário COMPLETO de produtos da empresa.
        """
        caixa = await self._get_caixa_ativo()

        # Remove itens inválidos (quantity == 0)
        await CartItem.filter(caixa_id=caixa.caixa_id, quantity=0).delete()

        produtos = await CartItem.filter(caixa_id=caixa.caixa_id).all()

        return [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": float(item.price),
                "total_price": float(item.total_price),
                "product_code": item.product_code,
            }
            for item in produtos
        ]

    async def remove_produto(self, product_id: int, empresa_id: int, employee_id: int) -> Dict[str, Any]:
        """
        Remove um produto do carrinho e restaura o estoque.
        """
        caixa = await self._get_caixa_ativo()

        # 🎯 CORREÇÃO: Usar .filter().first() em vez de .get_or_none() para evitar MultipleObjectsReturned
        cart_item = await CartItem.filter(caixa_id=caixa.caixa_id, product_id=product_id).first()

        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado no carrinho.")

        # Restaura estoque
        produto = await Produto.get_or_none(id=product_id, usuario_id=empresa_id)
        if produto:
            produto.stock += int(cart_item.quantity)
            await produto.save()

        await cart_item.delete()

        return {"success": True, "aviso": "Produto removido com sucesso."}

    async def limpar_carrinho(self, empresa_id: int, employee_id: int) -> dict:
        """
        Limpa todos os itens do carrinho e restaura os estoques (usado para cancelamento de venda/sessão).
        """
        caixa = await self._get_caixa_ativo()
        itens = await CartItem.filter(caixa_id=caixa.caixa_id).all()  # pega todos

        if not itens:
            return {"success": False, "aviso": "Nenhum item encontrado no carrinho."}

        for item in itens:
            # Busca o produto correspondente ao item
            produto = await Produto.filter(id=item.product_id, usuario_id=empresa_id).first()

            if produto:
                # Restaura o estoque
                produto.stock += int(item.quantity or 0)
                await produto.save()

        # Após restaurar os estoques, limpa o carrinho
        await CartItem.filter(caixa_id=caixa.caixa_id).delete()

        return {"success": True, "aviso": "Carrinho limpo e estoque restaurado."}

    async def limpar_carrinho_pos_venda(self, caixa_id: int) -> bool:
        """
        Limpa o carrinho após finalizar uma venda. NÃO RESTAURA ESTOQUE (venda consumiu o estoque).
        Este método é interno e usado pelo processo de finalização de venda.
        """
        itens = await CartItem.filter(caixa_id=caixa_id).all()

        if itens:
            await CartItem.filter(caixa_id=caixa_id).delete()
            return True

        return False