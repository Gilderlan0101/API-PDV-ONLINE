from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from tortoise.transactions import atomic
from tortoise.expressions import Q


# Certifique-se de que os imports estão corretos
from src.controllers.sales.sales import Checkout
from src.controllers.car.cart_control import CartManagerDB
from src.model.user import Usuario
from src.model.product import Produto
from src.model.sale import Sales

cart = CartManagerDB()


@atomic()
async def processar_venda_carrinho(
    user_id: int,  # Recebe o ID do usuário em vez do objeto completo
    cart_items: list,
    payment_method: str,
    employee_operator_id: int,
    customer_id: Optional[int] = None,
    installments: Optional[int] = None,
    cpf: Optional[str] = None,
    valor_recebido: Optional[float] = None,
    troco: Optional[float] = None,
) -> dict:
    """
    Processa todos os itens do carrinho em uma única transação
    """

    print("Iniciando processamento do carrinho...")

    itens_processados = []
    __saving_product_name = []
    total_geral = 0.0
    lucro_geral = 0.0
    cost_total_geral = 0.0  # <-- Nova variável para o custo total
    produto_id = None

    if not cart_items:
        return {"success": False, "error": "O carrinho está vazio."}

    try:
        # 🔹 Busca usuário dono da venda DENTRO da transação
        current_user = await Usuario.get_or_none(id=user_id)
        if not current_user:
            raise Exception("Usuário não encontrado.")

        print(f"👤 Usuário encontrado: {current_user.id}")

        # 🔹 Itera sobre cada item do carrinho
        for i, item in enumerate(cart_items):
            print(f"\n--- Processando Item {i} ---")

            product_code = item.get("product_code") if isinstance(item, dict) else getattr(item, "product_code", None)
            quantity = int(item.get("quantity", 1)) if isinstance(item, dict) else getattr(item, "quantity", 1)

            products_name = item.get("product_name") if isinstance(item, dict) else getattr(item, "product_name")

            __saving_product_name.append({products_name})

            if not product_code:
                print("❌ SKIP: Produto sem código")
                continue

            # 🔹 Buscar produto no banco (Com Q object para evitar erros)
            busca_produto = Q(usuario_id=current_user.id) & Q(product_code=product_code.strip().upper())
            produto = await Produto.filter(busca_produto).first()

            if not produto:
                print(f"❌ Produto não encontrado: {product_code}")
                continue

            # 🔹 Verificar estoque
            if (produto.stock or 0) < quantity:
                print(f"❌ Estoque insuficiente para {produto.name}")
                continue

            # 🔹 Atualizar estoque
            produto.stock -= quantity
            produto.atualizado_em = datetime.now()
            await produto.save()

            # 🔹 Calcular valores
            sale_price = float(produto.sale_price or 0.0)
            cost_price = float(produto.cost_price or 0.0)

            # ID do produto
            produto_id = produto.id

            total_price = quantity * sale_price
            lucro_total = (sale_price - cost_price) * quantity
            cost_total = quantity * cost_price  # <-- Calcula o custo do item

            # 🔹 Montar item da venda
            item_venda = {
                "product_name": produto.name,
                "quantity": quantity,
                "unit_price": sale_price,
                "total_price": total_price,
                "lucro_total": lucro_total,
                "cost_price": cost_price,
                "product_code": produto.product_code,
            }

            itens_processados.append(item_venda)
            total_geral += total_price
            lucro_geral += lucro_total
            cost_total_geral += cost_total  # <-- Acumula o custo total da venda

            print(f"✅ Item processado: {produto.name}")

    except Exception as e:
        print(f"❌ Erro ao processar itens: {e}")
        import traceback

        print(traceback.format_exc())
        return {"success": False, "error": f"Erro interno ao processar itens do carrinho: {str(e)}"}

    if not itens_processados:
        await cart.limpar_carrinho(user_id=user_id)
        return {"success": False, "error": f"Nenhum dos {len(cart_items)} itens pôde ser processado."}

    # 🔹 Criar checkout instance
    checkout_instance = Checkout()
    checkout_instance._set_receipt_data(itens_processados)
    checkout_instance.total_price = total_geral
    checkout_instance.lucro_total = lucro_geral
    checkout_instance.payment_method = payment_method.upper()

    # 🔹 Registrar venda única
    venda = await Sales.create(
        product_name=__saving_product_name,
        quantity=len(itens_processados),
        payment_method=payment_method.upper(),
        total_price=total_geral,
        lucro_total=lucro_geral,
        cost_price=cost_total_geral,  # <-- O CAMPO QUE FALTAVA
        produto_id=produto_id,
        usuario_id=current_user.id,
        funcionario_id=employee_operator_id,
        customer_id=customer_id,
        installments=installments,
        valor_recebido=valor_recebido,
        troco=troco,
    )

    checkout_instance.venda = venda
    checkout_instance.sale_code = f"V{venda.id:06d}"

    # Limpar carrinho
    await cart.limpar_carrinho(user_id=user_id)

    return {
        "success": True,
        "data": {
            "checkout_instance": checkout_instance,
            "total_venda": total_geral,
            "quantidade_itens": len(itens_processados),
            "itens_processados": itens_processados,
        },
    }
