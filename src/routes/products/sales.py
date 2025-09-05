from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from src.auth.deps import get_current_user
from src.model.user import Usuario
from src.controllers.sales.sales import Checkout
from src.controllers.stoke.stoke_control import gerar_relatorio_completo
from src.controllers.car.cart_control import CartManagerDB
from src.model.employee import Employees
from src.utils.sales_code_generator import gerar_codigo_venda
from src.controllers.sales.fetch_sales import get_sales
from src.controllers.sales.delete_sales import delete_or_update_product_sale


router = APIRouter()
cart = CartManagerDB()


@router.post("/finalizar", status_code=status.HTTP_200_OK)
async def finalizar_venda(
    payment_method: str = Query(..., description="Forma de pagamento: dinheiro, cartão, pix, nota"),
    funcionario_id: Optional[int] = Query(None),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        # 🔹 Inicializa admin e operador
        admin_user = current_user
        funcionario_operador_id = None
        funcionario_operador_nome = current_user.username

        # 🔹 VERIFICA SE current_user É UM FUNCIONÁRIO
        funcionario = await Employees.filter(id=current_user.id).first()
        if funcionario and funcionario.usuario:
            # ✅ Busca o usuário admin pelo ID do relacionamento
            admin_user = await Usuario.get(id=funcionario.id)
            funcionario_operador_id = funcionario.id
            funcionario_operador_nome = funcionario.nome
            print(f"DEBUG: Funcionário {funcionario.nome} pertence ao admin {admin_user.username}")

        # 🔹 SE FOI PASSADO funcionario_id (admin vendendo para funcionário)
        if funcionario_id:
            funcionario_extra = await Employees.filter(
                id=funcionario_id,
                usuario_id=admin_user.id,  # ✅ Verifica se funcionário pertence ao admin
            ).first()

            if funcionario_extra:
                funcionario_operador_id = funcionario_extra.id
                funcionario_operador_nome = funcionario_extra.nome
                print(f"DEBUG: Venda atribuída ao funcionário {funcionario_extra.nome}")
            else:
                print(f"DEBUG: Funcionário ID {funcionario_id} não pertence ao admin {admin_user.id}")

        # 🔹 Listar produtos do carrinho do admin dono
        produtos = await cart.listar_produtos(admin_user.id)
        if not produtos:
            return {"success": False, "data": None, "error": "Carrinho vazio"}

        # 🔹 Monta detalhes da venda
        total_venda = 0.0
        venda_detalhes = []
        for prod in produtos:
            total_venda += prod.price_total
            venda_detalhes.append(
                {
                    "produto_id": prod.product_id,
                    "nome": prod.product_name,
                    "quantidade": prod.quantity,
                    "preco_unitario": prod.price,
                }
            )

        sale_code = gerar_codigo_venda()
        notas_fiscais = []

        # 🔹 Processa cada produto do carrinho
        for prod in venda_detalhes:
            checkout = Checkout(
                user_id=admin_user.id,  # ✅ ID do admin dono
                product_name=prod["nome"],
                produto_id=prod["produto_id"],
                quantity=prod["quantidade"],
                total_price=prod["quantidade"] * prod["preco_unitario"],
                lucro_total=0.0,
                payment_method=payment_method.lower(),
                funcionario_id=funcionario_operador_id,  # ✅ ID do funcionário operador
                funcionario_nome=funcionario_operador_nome,
                sale_code=sale_code,
            )

            nota = await checkout.process_sale(
                current_user=admin_user,  # ✅ Objeto do admin
                product_code=str(prod["produto_id"]),
                quantity=prod["quantidade"],
                payment_method=payment_method,
                funcionario_id=funcionario_operador_id,
            )
            notas_fiscais.append(nota)

        # 🔹 Limpa o carrinho do admin e gera relatório
        await cart.limpar_carrinho(admin_user.id)
        relatorio = await gerar_relatorio_completo(admin_user.id)

        return {
            "success": True,
            "data": {
                "notas_fiscais": notas_fiscais,
                "relatorio": relatorio,
                "total_venda": total_venda,
                "codigo_da_venda": sale_code,
                "funcionario_operador_id": funcionario_operador_id,
                "funcionario_operador_nome": funcionario_operador_nome,
                "admin_id": admin_user.id,
            },
            "error": None,
        }

    except Exception as e:
        import traceback

        print(f"Traceback:\n{traceback.format_exc()}")
        return {"success": False, "data": None, "error": f"Erro inesperado: {str(e)}"}


@router.get('/buscar/venda')
async def buscar_venda(sale_code: str, current_user: Usuario = Depends(get_current_user)):
    """Buscar venda pelo código"""
    try:
        # ✅ Chamada correta da função assíncrona
        vendas = await get_sales(current_user.id, sale_code)

        # Transformar objetos de vendas em dicionário para retornar JSON
        resultado = [
            {
                "produto": venda.product_name,
                "quantidade": venda.quantity,
                "preco_unitario": float(venda.total_price / venda.quantity),
                "valor_total": float(venda.total_price),
                "lucro_total": float(venda.lucro_total),
                "codigo_da_venda": venda.sale_code,
            }
            for venda in vendas
        ]

        return {"success": True, "data": resultado, "error": None}

    except Exception as e:
        import traceback

        print(f"Erro em buscar_venda:\n{traceback.format_exc()}")
        return {"success": False, "data": None, "error": str(e)}


@router.delete('/deleta/venda/')
async def delete_sale(
    sale_code: str = Query(...),
    product_id: int = Query(...),
    quantity: Optional[int] = None,
    # current_user: Usuario = Depends(get_current_user)
):

    var = await delete_or_update_product_sale(1, sale_code, product_id, quantity)
    if var:
        return var
    else:
        return var
