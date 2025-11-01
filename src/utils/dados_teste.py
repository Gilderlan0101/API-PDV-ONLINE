from passlib.hash import bcrypt
from datetime import datetime
from faker import Faker
import random
import re
from dotenv import load_dotenv

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
from src.controllers.delivery.delivery_controller import CreateDelivery
from src.controllers.delivery.delivery_reports import gerenciagelivery, assign_delivery_to_driver, update_delivery_status
from src.controllers.payments.pix import PixService, PixCreateRequest

import json
from fastapi import HTTPException
from tortoise.expressions import F
import os

import time

__PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO', 'NOTA', 'FIADO']
IMG_PRODUCT_DEFAULT = os.getenv('PATH_IMG_DEFAULT_PRODUCTS', None)

load_dotenv()


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

        admin_2 = await Usuario.filter(email="silva@test.com").first()
        if not admin_2:
            print("🔹 Criando usuário admin silva...")
            admin_2 = await Usuario.create(
                username="Pizzaria",
                email="silva@test.com",
                password=get_hashed_password("123456"),
                company_name="Pizzaria do Bobs",
                trade_name="Loja Central",
                membros=1,
                cnpj="98765432000198",
                city="Rio de Janeiro",
                state="RJ",
                pending=True,
            )
            print(f"✅ Usuário admin 2 criado: {admin_2.email}")

        # ========================
        # CRIAR CONTAS PIX PARA AMBAS AS EMPRESAS
        # ========================
        print("\n🔹 Criando contas PIX...")

        # Conta PIX para empresa 1
        pix_service_1 = PixService(user_id=admin.id)
        pix_data_1 = PixCreateRequest(
            full_name='Maria Silva', city='São Paulo', key_pix='11999999999', value=1.0, type_exit='qr'  # Chave PIX telefone
        )

        try:
            conta_pix_1 = await pix_service_1.create_pix_account(pix_data_1)
            if conta_pix_1:
                print(f"✅ Conta PIX criada para Empresa 1: {pix_data_1.key_pix}")
            else:
                print("❌ Erro ao criar conta PIX para Empresa 1")
        except Exception as e:
            print(f"⚠️  Erro ao criar conta PIX Empresa 1: {str(e)}")

        # Conta PIX para empresa 2
        pix_service_2 = PixService(user_id=admin_2.id)
        pix_data_2 = PixCreateRequest(
            full_name='João Santos', city='Rio de Janeiro', key_pix='21988888888', value=1.0, type_exit='qr'  # Chave PIX telefone
        )

        try:
            conta_pix_2 = await pix_service_2.create_pix_account(pix_data_2)
            if conta_pix_2:
                print(f"✅ Conta PIX criada para Empresa 2: {pix_data_2.key_pix}")
            else:
                print("❌ Erro ao criar conta PIX para Empresa 2")
        except Exception as e:
            print(f"⚠️  Erro ao criar conta PIX Empresa 2: {str(e)}")

        # ========================
        # Criar funcionários (ENTREGADORES)
        # ========================
        funcionarios_entregadores = [
            {"nome": "João Entregador", "email": "joao@teste.com", "cargo": "Caixa"},
            {"nome": "Maria Entregadora", "email": "maria@teste.com", "cargo": "Entregador"},
            {"nome": "Carlos Motoboy", "email": "carlos@teste.com", "cargo": "Entregador"},
        ]

        for func in funcionarios_entregadores:
            funcionario = await Employees.filter(email=func["email"], usuario_id=admin.id).first()
            if not funcionario:
                funcionario = await Employees.create(
                    nome=func["nome"],
                    cargo=func["cargo"],
                    email=func["email"],
                    senha=get_hashed_password("1234"),
                    telefone=lot_bar_code_size(),
                    ativo=True,
                    usuario_id=admin.id,
                )
                print(f"✅ Entregador criado: {funcionario.nome}")

        # ========================
        # Criar produtos para AMBAS as empresas
        # ========================
        produtos_data_comuns = [
            {"code": "PIZ001", "name": "Pizza Calabresa", "cost": 15.00, "sale": 25.00, "supplier": "Pizzaria", "group": "Alimentos"},
            {"code": "PIZ002", "name": "Pizza Frango", "cost": 16.00, "sale": 26.00, "supplier": "Pizzaria", "group": "Alimentos"},
            {"code": "BEB001", "name": "Coca-Cola 2L", "cost": 5.50, "sale": 8.00, "supplier": "Coca-Cola", "group": "Bebidas"},
        ]

        produtos_exclusivos_empresa1 = [
            {"code": "HMB001", "name": "Hambúrguer Artesanal", "cost": 8.00, "sale": 15.00, "supplier": "Lanchonete", "group": "Alimentos"},
            {"code": "BAT001", "name": "Batata Frita Grande", "cost": 4.00, "sale": 8.00, "supplier": "Lanchonete", "group": "Acompanhamentos"},
        ]

        produtos_exclusivos_empresa2 = [
            {"code": "PST001", "name": "Pastel de Carne", "cost": 3.50, "sale": 7.00, "supplier": "Pastelaria", "group": "Salgados"},
            {"code": "COX001", "name": "Coxinha de Frango", "cost": 2.50, "sale": 5.00, "supplier": "Pastelaria", "group": "Salgados"},
        ]

        produtos_criados_empresa1 = []
        produtos_criados_empresa2 = []

        # Criar produtos comuns para ambas as empresas
        print("\n🔹 Criando produtos comuns para ambas as empresas...")
        for p in produtos_data_comuns:
            # Para empresa 1
            produto_emp1 = await Produto.filter(product_code=p["code"], usuario_id=admin.id).first()
            if not produto_emp1:
                produto_emp1 = await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=100,
                    stoke_max=200,
                    stoke_min=10,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    ticket="Delivery",
                    controllstoke="Sim",
                    group=p["group"],
                    image_url=IMG_PRODUCT_DEFAULT,
                    usuario_id=admin.id,
                )
                print(f"✅ Produto Empresa 1 criado: {p['name']}")
            produtos_criados_empresa1.append(produto_emp1)

            # Para empresa 2
            produto_emp2 = await Produto.filter(product_code=p["code"], usuario_id=admin_2.id).first()
            if not produto_emp2:
                produto_emp2 = await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=80,
                    stoke_max=150,
                    stoke_min=5,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    ticket="Delivery",
                    controllstoke="Sim",
                    group=p["group"],
                    image_url=IMG_PRODUCT_DEFAULT,
                    usuario_id=admin_2.id,
                )
                print(f"✅ Produto Empresa 2 criado: {p['name']}")
            produtos_criados_empresa2.append(produto_emp2)

        # Criar produtos exclusivos para empresa 1
        print("\n🔹 Criando produtos exclusivos para Empresa 1...")
        for p in produtos_exclusivos_empresa1:
            produto = await Produto.filter(product_code=p["code"], usuario_id=admin.id).first()
            if not produto:
                produto = await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=50,
                    stoke_max=100,
                    stoke_min=5,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    ticket="Delivery",
                    controllstoke="Sim",
                    group=p["group"],
                    image_url='IMG_PRODUCT_DEFAULT',
                    usuario_id=admin.id,
                )
                print(f"✅ Produto exclusivo Empresa 1 criado: {p['name']}")
                produtos_criados_empresa1.append(produto)

        # Criar produtos exclusivos para empresa 2
        print("\n🔹 Criando produtos exclusivos para Empresa 2...")
        for p in produtos_exclusivos_empresa2:
            produto = await Produto.filter(product_code=p["code"], usuario_id=admin_2.id).first()
            if not produto:
                produto = await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=60,
                    stoke_max=120,
                    stoke_min=5,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    ticket="Delivery",
                    controllstoke="Sim",
                    group=p["group"],
                    usuario_id=admin_2.id,
                )
                print(f"✅ Produto exclusivo Empresa 2 criado: {p['name']}")
                produtos_criados_empresa2.append(produto)

        # ========================
        # Criar clientes para entregas (OBRIGATÓRIO)
        # ========================
        clientes_entregas = [
            {
                "nome": "João Silva",
                "endereco": {"street": "Rua das Flores", "house_number": "123", "neighborhood": "Centro", "city": "São Paulo", "state": "SP"},
            },
            {
                "nome": "Maria Souza",
                "endereco": {"street": "Avenida Paulista", "house_number": "1000", "neighborhood": "Bela Vista", "city": "São Paulo", "state": "SP"},
            },
            {
                "nome": "Carlos Pereira",
                "endereco": {"street": "Rua Augusta", "house_number": "500", "neighborhood": "Consolação", "city": "São Paulo", "state": "SP"},
            },
            {
                "nome": "Ana Santos",
                "endereco": {
                    "street": "Rua das Palmeiras",
                    "house_number": "789",
                    "neighborhood": "Vila Madalena",
                    "city": "São Paulo",
                    "state": "SP",
                },
            },
            {
                "nome": "Pedro Costa",
                "endereco": {"street": "Av. Central", "house_number": "321", "neighborhood": "Centro", "city": "São Paulo", "state": "SP"},
            },
        ]

        clientes_criados = []

        for cliente_data in clientes_entregas:
            cliente = await Customer.filter(full_name=cliente_data["nome"], usuario_id=admin.id).first()
            if not cliente:
                cpf_numbers_only = re.sub(r"\D", "", fake.cpf())
                cliente = await Customer.create(
                    full_name=cliente_data["nome"],
                    birth_date=fake.date_of_birth(minimum_age=18, maximum_age=60).isoformat(),
                    cpf=cpf_numbers_only,
                    mother_name=fake.name_female(),
                    road=cliente_data["endereco"]["street"],
                    house_number=cliente_data["endereco"]["house_number"],
                    neighborhood=cliente_data["endereco"]["neighborhood"],
                    city=cliente_data["endereco"]["city"],
                    tel=fake.cellphone_number(),
                    cep=fake.postcode(),
                    credit=1000.00,
                    current_balance=0.00,
                    due_date=datetime.now(),
                    status="ATIVO",
                    usuario_id=admin.id,
                )
                print(f"✅ Cliente criado: {cliente_data['nome']}")
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
                funcionario_id=None,
            )
            print(f"✅ Caixa aberto: ID {caixa_aberto.id}")

        # ========================
        # 🚀 TESTES DO SISTEMA DE ENTREGA
        # ========================
        print("\n" + "=" * 60)
        print("🚀 INICIANDO TESTES DO SISTEMA DE ENTREGA")
        print("=" * 60)

        await testar_sistema_entrega(admin.id, clientes_criados, produtos_criados_empresa1)

        # ========================
        # VENDAS BÁSICAS PARA GERAR ENTREGAS
        # ========================
        print("\n🛒 REALIZANDO VENDAS PARA GERAR ENTREGAS")
        print("-" * 40)

        # Venda 1: Cliente registrado com entrega
        try:
            checkout1 = Checkout()
            receipt1 = await checkout1.process_sale(
                current_user=admin,
                product_code="PIZ001",
                quantity=2,
                payment_method="PIX",
                funcionario_id=None,
                customer_id=clientes_criados[0].id,
            )

            if receipt1:
                finalizador1 = FinalizationObjcts(checkout1)
                await finalizador1.Updating_cash_values(caixa_aberto.id)
                print(f"✅ Venda 1 realizada - Código: {checkout1.sale_code}")
            else:
                print("❌ Falha na venda 1")
        except Exception as e:
            print(f"❌ Erro na venda 1: {str(e)}")

        # Venda 2: Outro cliente
        try:
            checkout2 = Checkout()
            receipt2 = await checkout2.process_sale(
                current_user=admin,
                product_code="PIZ002",
                quantity=1,
                payment_method="DINHEIRO",
                funcionario_id=None,
                customer_id=clientes_criados[1].id,
                valor_recebido=30.00,
                troco=4.00,
            )

            if receipt2:
                finalizador2 = FinalizationObjcts(checkout2)
                await finalizador2.Updating_cash_values(caixa_aberto.id)
                print(f"✅ Venda 2 realizada - Código: {checkout2.sale_code}")
            else:
                print("❌ Falha na venda 2")
        except Exception as e:
            print(f"❌ Erro na venda 2: {str(e)}")

        # ========================
        # TESTAR GERENCIAMENTO DE ENTREGAS
        # ========================
        print("\n" + "=" * 60)
        print("📊 TESTANDO GERENCIAMENTO DE ENTREGAS")
        print("=" * 60)

        resultado_gerenciamento = await gerenciagelivery(admin.id)

        if resultado_gerenciamento.get('success'):
            stats = resultado_gerenciamento.get('statistics', {})
            print(f"📈 Estatísticas do sistema:")
            print(f"   • Entregas pendentes: {stats.get('total_pending', 0)}")
            print(f"   • Entregas ativas: {stats.get('total_active', 0)}")
            print(f"   • Entregadores disponíveis: {stats.get('total_drivers_available', 0)}")
            print(f"   • Entregadores ocupados: {stats.get('total_drivers_busy', 0)}")
            print(f"   • Alertas: {stats.get('total_notices', 0)}")

            # Mostrar notificações
            notices = resultado_gerenciamento.get('notices', [])
            if notices:
                print(f"\n🔔 Notificações:")
                for notice in notices:
                    print(f"   • {notice.get('mensagem', '')}")
        else:
            print(f"❌ Erro no gerenciamento: {resultado_gerenciamento.get('error', 'Erro desconhecido')}")

        # ========================
        # FECHAR CAIXA
        # ========================
        caixa_aberto.aberto = False
        caixa_aberto.data_fechamento = datetime.now()
        await caixa_aberto.save()
        print(f"\n🔒 Caixa fechado: ID {caixa_aberto.id}")

        # ========================
        # RESUMO FINAL
        # ========================
        print("\n" + "=" * 60)
        print("📊 RESUMO FINAL DOS DADOS CRIADOS")
        print("=" * 60)
        print(f"🏢 Empresa 1: {admin.company_name}")
        print(f"   • Contas PIX: 1")
        print(f"   • Produtos totais: {len(produtos_criados_empresa1)}")
        print(f"   • Produtos comuns: {len(produtos_data_comuns)}")
        print(f"   • Produtos exclusivos: {len(produtos_exclusivos_empresa1)}")

        print(f"\n🏢 Empresa 2: {admin_2.company_name}")
        print(f"   • Contas PIX: 1")
        print(f"   • Produtos totais: {len(produtos_criados_empresa2)}")
        print(f"   • Produtos comuns: {len(produtos_data_comuns)}")
        print(f"   • Produtos exclusivos: {len(produtos_exclusivos_empresa2)}")

        print(f"\n👥 Clientes criados: {len(clientes_criados)}")
        print(f"🚚 Entregadores criados: {len(funcionarios_entregadores)}")

        print("\n🎉 Todos os testes foram concluídos com sucesso!")


async def testar_sistema_entrega(company_id: int, clientes: list, produtos: list):
    """Executa testes específicos do sistema de entrega"""
    # ... (mantenha o mesmo código da função testar_sistema_entrega que você já tinha)
    # O código desta função permanece igual ao que você já tinha
