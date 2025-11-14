from typing import Any, Dict, List
from fastapi import HTTPException, status
from src.model.product import Produto
from src.model.carItems import CartItem
from src.model.caixa import Caixa
import locale


locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


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
            # Busca usando as duas chaves: usuario_id (empresa) e funcionario_id
            caixa = await Caixa.filter(
                usuario_id=self.company_id, 
                funcionario_id=self.employee_id, 
                aberto=True
                ).first()

            if not caixa:
                # Erro 400 se o caixa não estiver aberto.
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum caixa aberto encontrado para este funcionário/empresa.")

            return caixa

        except HTTPException:
            raise
        except Exception as e:
            #  Erro 500 para falhas inesperadas de banco
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar caixa: {str(e)}")



    async def add_produto(self, product_id: int, quantity: int, empresa_id: int, employee_id: int) -> Dict[str, Any]:
        caixa = await self._get_caixa_ativo()

        produto = await Produto.filter(
            id=product_id, active=True, usuario_id=empresa_id
        ).select_related('usuario').first()

        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")

        quantity = int(quantity)
        
        if produto.stock < quantity:
            raise HTTPException(status_code=400, detail="Estoque insuficiente.")

        # Verifica se já existe no carrinho
        cart_item = await CartItem.filter(
            caixa_id=caixa.caixa_id, 
            product_id=product_id
        ).first()

        if cart_item:
            # 🎯 DEBUG: Verificar o cart_item existente
            print(f"🔍 CART_ITEM EXISTENTE:")
            print(f"  ID: {cart_item.id}")
            print(f"  Quantity atual: {cart_item.quantity}")
            
            quantidade_atual = int(cart_item.quantity)
            nova_quantidade = quantidade_atual + quantity
            
            return await self.update_produto(
                int(product_id), 
                nova_quantidade, 
                int(empresa_id)
            )

        # 🎯 CRIAR NOVO CARTITEM COM DEBUG
        try:
            cart_item = await CartItem.create(
                caixa_id=caixa.caixa_id,
                product_id=product_id,
                product_name=produto.name,
                quantity=quantity,
                price=float(produto.sale_price),
                total_price=float(produto.sale_price) * quantity,
                product_code=produto.product_code,
            )
            
            print(f"✅ NOVO CART_ITEM CRIADO:")
            print(f"  ID: {cart_item.id}")
            print(f"  Quantity: {cart_item.quantity}")
            
        except Exception as e:
            print(f"❌ ERRO AO CRIAR CART_ITEM: {e}")
            raise

        # Atualiza estoque
        produto.stock -= quantity
        await produto.save()

        return {
            "success": True,
            "item_adicionado": {
                "id": cart_item.id,  # 🎯 Usar o ID real
                "product_id": cart_item.product_id,
                "product_name": cart_item.product_name,
                "quantity": int(cart_item.quantity),
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

        cart_item = await CartItem.filter(
            caixa_id=caixa.caixa_id, 
            product_id=product_id
        ).first()
        
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Produto não encontrado no carrinho."
            )

        produto = await Produto.get_or_none(id=product_id, usuario_id=empresa_id)
        
        # ✅ CORREÇÃO: Garantir que todos sejam inteiros
        old_quantity = int(cart_item.quantity)  # Força conversão para int
        new_quantity = int(new_quantity)        # Garante que é int
        quantity_difference = new_quantity - old_quantity

        print(f"🔍 DEBUG UPDATE:")
        print(f"  old_quantity: {old_quantity} (type: {type(old_quantity)})")
        print(f"  new_quantity: {new_quantity} (type: {type(new_quantity)})")
        print(f"  difference: {quantity_difference}")

        if new_quantity <= 0:
            # Remove o item se quantidade for zero ou negativa
            if produto:
                produto.stock += old_quantity  # Restaura estoque
                await produto.save()
            await cart_item.delete()
            return {
                "success": True, 
                "aviso": "Produto removido do carrinho por quantidade zero."
            }

        if produto:
            # Verifica estoque apenas se está aumentando a quantidade
            if quantity_difference > 0 and produto.stock < quantity_difference:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Estoque insuficiente para aumentar a quantidade."
                )

            # Ajusta o estoque
            produto.stock -= quantity_difference
            await produto.save()

        # ✅ CORREÇÃO: Garantir tipos numéricos
        cart_item.quantity = new_quantity
        cart_item.total_price = float(cart_item.price) * new_quantity
        await cart_item.save()

        return {
            "success": True,
            "item_atualizado": {
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "product_name": cart_item.product_name,
                "quantity": int(cart_item.quantity),  # ✅ Garante int na resposta
                "price": float(cart_item.price),
                "total_price": float(cart_item.total_price),
            },
        }




    async def listar_produtos(self, empresa_id: int, employee_id: int) -> List[Dict[str, Any]]:
        caixa = await self._get_caixa_ativo()
        
        await CartItem.filter(caixa_id=caixa.caixa_id, quantity=0).delete()

        produtos = await CartItem.filter(caixa_id=caixa.caixa_id).all()
        
        agrupados = {}
        for item in produtos:
            key = item.product_id
            if key in agrupados:
                # ✅ CORREÇÃO: Converter para int antes de somar
                agrupados[key]['quantity'] += int(item.quantity)
                agrupados[key]['total_price'] += float(item.total_price)
            else:
                agrupados[key] = {
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'quantity': int(item.quantity),  # ✅ Converter para int
                    'price': float(item.price),
                    'total_price': float(item.total_price),
                    'product_code': item.product_code,
                }
        
        lista_final = list(agrupados.values())
        
        return [
            {
                "id": idx + 1,
                "product_id": item['product_id'],
                "product_name": item['product_name'],
                "quantity": item['quantity'],  # ✅ Agora é int
                "price": item['price'],
                "total_price": locale.currency(float(item['total_price']), grouping=True, symbol=False),
                "product_code": item['product_code'],
            }
            for idx, item in enumerate(lista_final)
        ]

    async def remove_produto(self, product_id: int, empresa_id: int, employee_id: int) -> Dict[str, Any]:
        """
        Remove TODAS as ocorrências de um produto do carrinho.
        """
        caixa = await self._get_caixa_ativo()

        # Busca todos os itens do produto
        cart_items = await CartItem.filter(
            caixa_id=caixa.caixa_id, 
            product_id=product_id
        ).all()

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Produto não encontrado no carrinho."
            )

        # Soma todas as quantidades
        quantidade_total = sum(int(item.quantity) for item in cart_items)
        product_name = cart_items[0].product_name

        # Restaura estoque
        produto = await Produto.get_or_none(id=product_id, usuario_id=empresa_id)
        if produto:
            produto.stock += quantidade_total
            await produto.save()

        # Deleta TODOS os registros
        deleted_count = await CartItem.filter(
            caixa_id=caixa.caixa_id, 
            product_id=product_id
        ).delete()

        return {
            "success": True, 
            "aviso": "Produto removido com sucesso.",
            "detalhes": {
                "product_id": product_id,
                "product_name": product_name,
                "quantidade_restaurada": quantidade_total,
                "itens_removidos": deleted_count
            }
        }
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
