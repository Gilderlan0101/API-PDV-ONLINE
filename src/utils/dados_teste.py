from passlib.hash import bcrypt
from datetime import datetime
from faker import Faker
import re
import random
from tortoise.transactions import in_transaction
from src.model.partial import Partial
from src.auth.auth_jwt import get_hashed_password
from src.model.product import Produto
from src.model.user import Membro, Usuario
from src.model.customers import Customer
from src.model.employee import Employees
from src.model.caixa import Caixa
from src.model.cashmovement import CashMovement
from src.controllers.sales.sales import Checkout
from src.controllers.car.cart_control import CartManagerDB
from src.controllers.payments.partial import PartialPayment
from src.utils.sales_code_generator import lot_bar_code_size
from src.controllers.sales.services import processar_venda_carrinho
from src.controllers.caixa.cash_controller import FinalizationObjcts
import json
from fastapi import HTTPException
from tortoise.expressions import F

import time
__PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO', 'NOTA', 'FIADO']


async def create_mock_data_and_sell_all_stock():
    """Cria dados mockados e realiza vendas de todo o estoque com diferentes métodos de pagamento"""
    fake = Faker("pt_BR")

    async with in_transaction() as conn:
        # ========================
        # Criar usuário admin
        # ========================
        admin = await Usuario.filter(email="admin@test.com").first()
        if not admin:
            print("🔹 Criando usuário admin...")
            admin = await Usuario.create(
                username="admin",
                email="admin@test.com",
                password=get_hashed_password("123456"),
                company_name="Empresa Teste 1",
                trade_name="Loja Central",
                membros=1,
                cnpj="12345638000199",
                city="São Paulo",
                state="SP",
                pending=True,
            )

            
            print(f"✅ Usuário admin criado: {admin.email}")
            
            time.sleep(2)

        admin_2 = await Usuario.filter(email="gilderlan@gmail.com").first()
        if not admin_2:
            print('Criando um novo usuário')
            admin_2 =  await Usuario.create(

                username="Gilderlan",
                email="gilderlan@gmail.com",
                password=get_hashed_password("123456"),
                company_name="Games 3D",
                trade_name="Loja Central",
                membros=0,
                cnpj="12445638000199",
                city="São Paulo",
                state="SP",
                pending=True,
                )

            print(f"Usuario admin_2 criado {admin_2.email}")

        # ========================
        # Criar funcionários
        # ========================
        funcionarios_emails = ["gilderlan@teste.com", "maria@teste.com", "gilvan@teste.com"]
        funcionarios_emails_admin_2 = ["otavio@teste.com", "santos@teste.com", "maicon@teste.com"]

        funcionarios_criados = []

        for email in funcionarios_emails:
            funcionario = await Employees.filter(email=email, usuario_id=admin.id).first()
            if not funcionario:
                funcionario = await Employees.create(
                    nome=email.split("@")[0].capitalize(),
                    cargo="Funcionário",
                    email=email,
                    senha=get_hashed_password("1234"),
                    telefone=lot_bar_code_size(),
                    ativo=True,
                    usuario_id=admin.id,
                )

                
                print(f"✅ Funcionário criado: {funcionario.nome}")
            funcionarios_criados.append(funcionario)

        for email in funcionarios_emails_admin_2:
            funcionario_admin_2 = await Employees.filter(email=email, usuario_id=admin_2.id).first()
            if not funcionario_admin_2:
                funcionario_admin_2 = await Employees.create(
                    nome=email.split("@")[0].capitalize(),
                    cargo="Funcionário",
                    email=email,
                    senha=get_hashed_password("1234"),
                    telefone=lot_bar_code_size(),
                    ativo=True,
                    usuario_id=admin_2.id,
                )

                print(f"✅ Funcionário criado: {funcionario_admin_2.nome}")
                print("Funcionarios de admin 2")


        funcionario_venda = funcionarios_criados[0] if funcionarios_criados else None

        # ========================
        # Criar produtos (20 produtos variados)
        # ========================
        produtos_data = [
            # Bebidas
            {"code": "BEB001", "name": "Coca-Cola 2L", "cost": 5.50, "sale": 8.00, "supplier": "Coca-Cola", "group": "Bebidas"},
            {"code": "BEB002", "name": "Suco de Laranja 1L", "cost": 4.00, "sale": 6.50, "supplier": "Del Valle", "group": "Bebidas"},
            {"code": "BEB003", "name": "Água Mineral 500ml", "cost": 1.00, "sale": 2.50, "supplier": "Crystal", "group": "Bebidas"},
            {"code": "BEB004", "name": "Cerveja Heineken 600ml", "cost": 6.00, "sale": 9.00, "supplier": "Heineken", "group": "Bebidas"},
            {"code": "BEB005", "name": "Energético Red Bull", "cost": 7.50, "sale": 12.00, "supplier": "Red Bull", "group": "Bebidas"},
            # Alimentos
            {"code": "ALI001", "name": "Arroz 5kg", "cost": 18.00, "sale": 25.00, "supplier": "Tio João", "group": "Alimentos"},
            {"code": "ALI002", "name": "Feijão 1kg", "cost": 8.00, "sale": 12.00, "supplier": "Camil", "group": "Alimentos"},
            {"code": "ALI003", "name": "Óleo de Soja 900ml", "cost": 5.00, "sale": 8.00, "supplier": "Liza", "group": "Alimentos"},
            {"code": "ALI004", "name": "Macarrão Espaguete 500g", "cost": 3.50, "sale": 6.00, "supplier": "Renata", "group": "Alimentos"},
            {"code": "ALI005", "name": "Açúcar 1kg", "cost": 3.00, "sale": 5.00, "supplier": "União", "group": "Alimentos"},
            # Limpeza
            {"code": "LIM001", "name": "Detergente 500ml", "cost": 1.50, "sale": 3.00, "supplier": "Ypê", "group": "Limpeza"},
            {"code": "LIM002", "name": "Sabão em Pó 1kg", "cost": 8.50, "sale": 12.00, "supplier": "Omo", "group": "Limpeza"},
            {"code": "LIM003", "name": "Amaciante 2L", "cost": 7.00, "sale": 10.00, "supplier": "Comfort", "group": "Limpeza"},
            {"code": "LIM004", "name": "Desinfetante 1L", "cost": 4.00, "sale": 6.50, "supplier": "Pinho Sol", "group": "Limpeza"},
            # Higiene
            {"code": "HIG001", "name": "Sabonete", "cost": 1.20, "sale": 2.50, "supplier": "Dove", "group": "Higiene"},
            {"code": "HIG002", "name": "Pasta de Dente", "cost": 2.50, "sale": 4.50, "supplier": "Colgate", "group": "Higiene"},
            {"code": "HIG003", "name": "Shampoo 300ml", "cost": 6.00, "sale": 9.00, "supplier": "Head & Shoulders", "group": "Higiene"},
            {"code": "HIG004", "name": "Condicionador 300ml", "cost": 6.00, "sale": 9.00, "supplier": "Seda", "group": "Higiene"},
            # Diversos
            {"code": "DIV001", "name": "Pilhas AA", "cost": 4.00, "sale": 7.00, "supplier": "Duracell", "group": "Diversos"},
            {"code": "DIV002", "name": "Fita Adesiva", "cost": 2.00, "sale": 4.00, "supplier": "Scotch", "group": "Diversos"},
        ]

        tickets = ["Novo", "Promoção", "Ofertas", "Destaques"]
        produtos_criados = []

        for p in produtos_data:
            produto = await Produto.filter(product_code=p["code"], usuario_id=admin.id).first()
            if not produto:
                stock_inicial = random.choice([10, 1000, 110, 900, 600, 60, 500, 100, 300])
                produto = await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=stock_inicial,
                    stoke_max=stock_inicial * 2,
                    stoke_min=5,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    ticket=random.choice(tickets),
                    controllstoke="Sim",
                    group=p["group"],
                    usuario_id=admin.id,
                )
                print(f"✅ Produto criado: {p['name']} - Estoque: {stock_inicial}")
            else:
                print(f"📦 Produto existente: {p['name']} - Estoque: {produto.stock}")

            produtos_criados.append(produto)

        # ========================
        # Criar clientes
        # ========================
        clientes_nomes = ["João Silva", "Maria Souza", "Carlos Pereira", "Ana Santos", "Pedro Costa"]
        clientes_criados = []

        for nome in clientes_nomes:
            cliente = await Customer.filter(full_name=nome, usuario_id=admin.id).first()
            if not cliente:
                cpf_numbers_only = re.sub(r"\D", "", fake.cpf())
                cliente = await Customer.create(
                    full_name=nome,
                    birth_date=fake.date_of_birth(minimum_age=18, maximum_age=60).isoformat(),
                    cpf=cpf_numbers_only,
                    mother_name=fake.name_female(),
                    road=fake.street_name(),
                    house_number=random.randint(1, 999),
                    neighborhood=fake.bairro(),
                    city=fake.city(),
                    tel=fake.cellphone_number(),
                    cep=fake.postcode(),
                    credit=1000.00,
                    current_balance=0.00,
                    due_date=datetime.now(),
                    status="ATIVO",
                    usuario_id=admin.id,
                )
                print(f"✅ Cliente criado: {nome}")
                clientes_criados.append(cliente)

        # ========================
        # ABRIR CAIXA PARA VENDAS
        # ========================
        print("\n💰 Abrindo caixa para processar vendas...")

        caixa_aberto = await Caixa.filter(usuario_id=admin.id, aberto=True).first()
        if not caixa_aberto:
            caixa_aberto = await Caixa.create(
                saldo_inicial=1000.00,
                saldo_atual=1000.00,
                aberto=True,
                data_abertura=datetime.now(),
                usuario_id=admin.id,
                funcionario_id=funcionario_venda.id if funcionario_venda else None,
            )
            print(f"✅ Caixa aberto: ID {caixa_aberto.id} - Saldo: R$ {caixa_aberto.saldo_atual:.2f}")
        else:
            print(f"📊 Caixa já aberto: ID {caixa_aberto.id} - Saldo: R$ {caixa_aberto.saldo_atual:.2f}")

        # ========================
        # 🎯 PROCESSAR VENDAS DE TODO O ESTOQUE
        # ========================
        print("\n" + "=" * 60)
        print("🛒 INICIANDO VENDAS DE TODO O ESTOQUE")
        print("=" * 60)

        cart_manager = CartManagerDB()
        vendas_realizadas = 0
        valor_total_vendas = 0.0

        # Agrupar produtos por método de pagamento
        grupos_pagamento = {
            'DINHEIRO': produtos_criados[0:5],  # Primeiros 5 produtos para DINHEIRO
            'PIX': produtos_criados[5:10],  # Próximos 5 para PIX
            'CARTAO': produtos_criados[10:15],  # Próximos 5 para CARTAO
            'NOTA': produtos_criados[15:20],  # Últimos 5 para NOTA
        }

        for metodo_pagamento, produtos in grupos_pagamento.items():
            print(f"\n💳 PROCESSANDO VENDAS COM {metodo_pagamento}")
            print("-" * 40)

            for produto in produtos:
                if produto.stock > 0:
                    try:
                        quantidade_venda = produto.stock  # Vender todo o estoque

                        print(f"📦 Vendendo {quantidade_venda} unidades de {produto.name}")

                        # Configurar valores para diferentes métodos de pagamento
                        valor_total = produto.sale_price * quantidade_venda
                        valor_recebido = None
                        troco = None
                        customer_id = None
                        installments = None

                        if metodo_pagamento == 'DINHEIRO':
                            valor_recebido = valor_total + 20.00  # Dar troco
                            troco = 20.00
                        elif metodo_pagamento == 'CARTAO':
                            installments = random.choice([1, 2, 3])  # 1 à 3 parcelas
                        elif metodo_pagamento == 'NOTA':
                            customer_id = random.choice(clientes_criados).id if clientes_criados else None

                        # Processar venda individual usando Checkout
                        checkout_processor = Checkout()

                        receipt, status_ok = await checkout_processor.process_sale(
                            current_user=admin,
                            product_code=produto.product_code,
                            quantity=quantidade_venda,
                            payment_method=metodo_pagamento,
                            funcionario_id=funcionario_venda.id if funcionario_venda else None,
                            customer_id=customer_id,
                            installments=installments,
                            valor_recebido=valor_recebido,
                            troco=troco,
                        )

                        if status_ok:
                            # Atualizar caixa usando FinalizationObjcts
                            finalizador = FinalizationObjcts(checkout_processor)
                            await finalizador.Updating_cash_values(caixa_aberto.id)

                            vendas_realizadas += 1
                            valor_total_vendas += valor_total

                            print(f"✅ Venda realizada: {produto.name}")
                            print(f"   Quantidade: {quantidade_venda}")
                            print(f"   Total: R$ {valor_total:.2f}")
                            print(f"   Método: {metodo_pagamento}")
                            if checkout_processor.sale_code:
                                print(f"   Código: {checkout_processor.sale_code}")

                            # Atualizar produto após venda
                            produto_apos_venda = await Produto.get(id=produto.id)
                            print(f"   Estoque atual: {produto_apos_venda.stock}")

                        else:
                            print(f"❌ Falha na venda: {produto.name}")

                    except HTTPException as e:
                        print(f"❌ Erro HTTP na venda de {produto.name}: {e.detail}")
                    except Exception as e:
                        print(f"❌ Erro inesperado na venda de {produto.name}: {str(e)}")
                        import traceback

                        print(f"Traceback: {traceback.format_exc()}")

                else:
                    print(f"⏭️  Produto sem estoque: {produto.name}")

        # ========================
        # VENDAS EM LOTE (CARRINHO) - Vender produtos restantes em grupos
        # ========================
        print("\n🛒 PROCESSANDO VENDAS EM LOTE (CARRINHO)")
        print("-" * 50)

        # Buscar produtos que ainda têm estoque
        produtos_com_estoque = await Produto.filter(usuario_id=admin.id, stock__gt=0).all()

        if produtos_com_estoque:
            # Criar grupos de produtos para vendas em lote
            grupos_carrinho = []
            grupo_atual = []

            for produto in produtos_com_estoque:
                if len(grupo_atual) < 3:  # Grupos de 3 produtos
                    grupo_atual.append(
                        {
                            "product_code": produto.product_code,
                            "product_name": produto.name,
                            "quantity": min(produto.stock, 30),  # Vender no máximo 2 de cada para teste
                            "unit_price": float(produto.sale_price),
                        }
                    )
                else:
                    grupos_carrinho.append(grupo_atual)
                    grupo_atual = [
                        {
                            "product_code": produto.product_code,
                            "product_name": produto.name,
                            "quantity": min(produto.stock, 30),
                            "unit_price": float(produto.sale_price),
                        }
                    ]

            if grupo_atual:
                grupos_carrinho.append(grupo_atual)

            # Processar cada grupo como uma venda de carrinho
            for i, grupo in enumerate(grupos_carrinho):
                metodo_carrinho = random.choice(__PAYMENT_METHODS)
                print(f"\n🛍️  Processando lote {i+1} com {len(grupo)} produtos ({metodo_carrinho})")

                try:
                    resultado = await processar_venda_carrinho(
                        user_id=admin.id,
                        cart_items=grupo,
                        payment_method=metodo_carrinho,
                        employee_operator_id=funcionario_venda.id if funcionario_venda else None,
                        customer_id=random.choice(clientes_criados).id if clientes_criados else None,
                        installments=random.choice([1, 2]) if metodo_carrinho == 'CARTAO' else None,
                        valor_recebido=(
                            sum(item['unit_price'] * item['quantity'] for item in grupo) + 10.00 if metodo_carrinho == 'DINHEIRO' else None
                        ),
                        troco=10.00 if metodo_carrinho == 'DINHEIRO' else None,
                    )

                    if resultado.get("success"):
                        vendas_realizadas += 1
                        valor_lote = sum(item['unit_price'] * item['quantity'] for item in grupo)
                        valor_total_vendas += valor_lote
                        print(f"✅ Lote {i+1} vendido com sucesso!")
                        print(f"   Valor do lote: R$ {valor_lote:.2f}")

                        # Atualizar caixa
                        if 'data' in resultado and 'checkout_instance' in resultado['data']:
                            finalizador = FinalizationObjcts(resultado['data']['checkout_instance'])
                            await finalizador.Updating_cash_values(caixa_aberto.id)
                    else:
                        print(f"❌ Falha no lote {i+1}: {resultado.get('error', 'Erro desconhecido')}")

                except Exception as e:
                    print(f"❌ Erro no lote {i+1}: {str(e)}")

        # ========================
        # RELATÓRIO FINAL
        # ========================
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DE VENDAS")
        print("=" * 60)

        # Verificar estoque final
        produtos_finais = await Produto.filter(usuario_id=admin.id).all()
        estoque_final = sum(prod.stock for prod in produtos_finais)
        produtos_zerados = sum(1 for prod in produtos_finais if prod.stock == 0)

        # Verificar saldo final do caixa
        caixa_final = await Caixa.get(id=caixa_aberto.id)

        print(f"✅ Vendas realizadas: {vendas_realizadas}")
        print(f"💰 Valor total em vendas: R$ {valor_total_vendas:.2f}")
        print(f"📦 Estoque final: {estoque_final} unidades")
        print(f"🔄 Produtos com estoque zerado: {produtos_zerados}/{len(produtos_finais)}")
        print(f"💵 Saldo inicial do caixa: R$ 1000.00")
        print(f"💵 Saldo final do caixa: R$ {caixa_final.saldo_atual:.2f}")
        print(f"📈 Lucro no caixa: R$ {caixa_final.saldo_atual - 1000.00:.2f}")

        # Fechar o caixa
        caixa_final.aberto = False
        caixa_final.data_fechamento = datetime.now()
        await caixa_final.save()
        print(f"🔒 Caixa fechado: ID {caixa_final.id}")

        print("\n🎉 Processo de vendas concluído com sucesso!")
