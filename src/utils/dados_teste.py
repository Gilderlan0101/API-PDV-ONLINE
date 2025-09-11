from passlib.hash import bcrypt
from datetime import datetime, timedelta
import random
import re
from faker import Faker
from tortoise.transactions import in_transaction

from src.auth.auth_jwt import get_hashed_password
from src.controllers.caixa.cash_controller import CashController
from src.controllers.sales.separate_payment_methods import separating_sales_by_payments
from src.model.product import Produto
from src.model.user import Membro, Usuario
from src.model.customers import Customer
from src.model.sale import Sales
from src.model.employee import Employees
from src.utils.sales_code_generator import barcode_generator


async def create_mock_data():
    """Cria usuário admin, funcionários, produtos, clientes e vendas mockadas."""
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
                password=bcrypt.hash("123456"),
                company_name="Empresa Teste 1",
                trade_name="Loja Central",
                membros=1,
                cnpj="12345678000199",
                city="São Paulo",
                state="SP",
            )
            await Membro.create(
                nome="Filial Centro",
                email='membro@test.com',
                senha=get_hashed_password('1234'),
                ativo=True,
                gerente="João",
                usuario_id=admin.id,
            )
            print(f"✅ Usuário admin criado: {admin.email}")

        # ========================
        # Criar funcionários
        # ========================
        funcionarios_existentes = await Employees.filter(usuario_id=admin.id).all()
        if not funcionarios_existentes:
            print("🔹 Criando funcionários...")
            for _ in range(3):
                funcionario = await Employees.create(
                    nome=fake.first_name(),
                    cargo=random.choice(["Caixa", "Vendedor", "Estoquista"]),
                    email=fake.email(),
                    senha=get_hashed_password('1234'),

                    ativo=True,
                    usuario_id=admin.id,
                )
                print(f"✅ Funcionário criado: {funcionario.nome}")
            funcionarios_existentes = await Employees.filter(usuario_id=admin.id).all()

        print("🔹 Criando caixas para funcionários...")
        for funcionario in funcionarios_existentes:
            try:
                caixa = await CashController.abrir_caixa(
                    usuario_id=admin.id, funcionario_id=funcionario.id, saldo_inicial=100.0, nome=f"Caixa {funcionario.nome}"
                )
                print(f"✅ Caixa criado para {funcionario.nome}: R$ {caixa.saldo_inicial}")
            except Exception as e:
                print(f"⚠️  Caixa já existe para {funcionario.nome}: {e}")

        # ========================
        # Criar produtos
        # ========================
        produtos_existentes = await Produto.filter(usuario_id=admin.id).all()
        if len(produtos_existentes) < 20:
            print("🔹 Criando 20 produtos...")
            produtos_data = [
                {
                    "code": "BEB001",
                    "name": "Coca-Cola 2L",
                    "cost": 5.50,
                    "sale": 8.00,
                    "supplier": "Coca-Cola",
                },
                {
                    "code": "BEB002",
                    "name": "Suco de Laranja 1L",
                    "cost": 4.00,
                    "sale": 6.50,
                    "supplier": "Del Valle",
                },
                {
                    "code": "BEB003",
                    "name": "Água Mineral 500ml",
                    "cost": 1.00,
                    "sale": 2.50,
                    "supplier": "Crystal",
                },
                {
                    "code": "BEB004",
                    "name": "Cerveja Heineken 600ml",
                    "cost": 6.00,
                    "sale": 9.00,
                    "supplier": "Heineken",
                },
                {
                    "code": "BEB005",
                    "name": "Energético Red Bull",
                    "cost": 7.50,
                    "sale": 12.00,
                    "supplier": "Red Bull",
                },
                {
                    "code": "ALI001",
                    "name": "Arroz 5kg",
                    "cost": 18.00,
                    "sale": 25.00,
                    "supplier": "Tio João",
                },
                {
                    "code": "ALI002",
                    "name": "Feijão 1kg",
                    "cost": 8.00,
                    "sale": 12.00,
                    "supplier": "Camil",
                },
                {
                    "code": "ALI003",
                    "name": "Açúcar 5kg",
                    "cost": 12.00,
                    "sale": 18.00,
                    "supplier": "União",
                },
                {
                    "code": "ALI004",
                    "name": "Óleo de Soja 900ml",
                    "cost": 5.00,
                    "sale": 8.00,
                    "supplier": "Liza",
                },
                {
                    "code": "ALI005",
                    "name": "Macarrão Espaguete 500g",
                    "cost": 3.50,
                    "sale": 6.00,
                    "supplier": "Renata",
                },
                {
                    "code": "LIM001",
                    "name": "Detergente 500ml",
                    "cost": 1.50,
                    "sale": 3.00,
                    "supplier": "Ypê",
                },
                {
                    "code": "LIM002",
                    "name": "Sabão em Pó 1kg",
                    "cost": 8.00,
                    "sale": 12.00,
                    "supplier": "OMO",
                },
                {
                    "code": "LIM003",
                    "name": "Amaciante 2L",
                    "cost": 9.00,
                    "sale": 15.00,
                    "supplier": "Comfort",
                },
                {
                    "code": "LIM004",
                    "name": "Desinfetante 1L",
                    "cost": 4.50,
                    "sale": 7.50,
                    "supplier": "Pinho Sol",
                },
                {
                    "code": "LIM005",
                    "name": "Esponja de Aço",
                    "cost": 0.80,
                    "sale": 2.00,
                    "supplier": "Bombril",
                },
                {
                    "code": "HIG001",
                    "name": "Pasta de Dente 90g",
                    "cost": 3.00,
                    "sale": 5.50,
                    "supplier": "Colgate",
                },
                {
                    "code": "HIG002",
                    "name": "Sabonete 90g",
                    "cost": 1.20,
                    "sale": 2.50,
                    "supplier": "Dove",
                },
                {
                    "code": "HIG003",
                    "name": "Shampoo 350ml",
                    "cost": 8.00,
                    "sale": 14.00,
                    "supplier": "Head & Shoulders",
                },
                {
                    "code": "HIG004",
                    "name": "Papel Higiênico 4un",
                    "cost": 4.00,
                    "sale": 7.00,
                    "supplier": "Neve",
                },
                {
                    "code": "HIG005",
                    "name": "Fio Dental 50m",
                    "cost": 2.50,
                    "sale": 4.50,
                    "supplier": "Oral-B",
                },
            ]
            for p in produtos_data:
                await Produto.create(
                    product_code=p["code"],
                    name=p["name"],
                    stock=random.randint(50, 200),
                    stoke_max=300,
                    stoke_min=20,
                    cost_price=p["cost"],
                    price_uni=p["cost"] * 1.2,
                    sale_price=p["sale"],
                    supplier=p["supplier"],
                    usuario_id=admin.id,
                )
            print("✅ 20 produtos criados!")

        # ========================
        # Criar clientes
        # ========================
        clientes_existentes = await Customer.filter(usuario_id=admin.id).all()
        if len(clientes_existentes) < 30:
            print("🔹 Criando 30 clientes...")
            for _ in range(30):
                cpf_numbers_only = re.sub(r"\D", "", fake.cpf())
                await Customer.create(
                    full_name=fake.name(),
                    birth_date=fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                    cpf=cpf_numbers_only,
                    mother_name=fake.name_female(),
                    road=fake.street_name(),
                    house_number=random.randint(1, 1000),
                    neighborhood=fake.bairro(),
                    city=fake.city(),
                    tel=fake.cellphone_number(),
                    cep=fake.postcode(),
                    credit=round(random.uniform(100, 1000), 2),
                    current_balance=round(random.uniform(0, 500), 2),
                    due_date=(datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
                    status=random.choices(['ATIVO', 'ATRASO', 'PENDENTE']),
                    usuario_id=admin.id,
                )
            print("✅ 30 clientes criados!")

        # ========================
        # Criar vendas
        # ========================
        vendas_existentes = await Sales.filter(usuario_id=admin.id).all()
        if len(vendas_existentes) < 50:
            print("🔹 Criando 50 vendas...")
            produtos = await Produto.filter(usuario_id=admin.id).all()
            clientes = await Customer.filter(usuario_id=admin.id).all()
            funcionarios = await Employees.filter(usuario_id=admin.id).all()

            for i in range(50):
                produto = random.choice(produtos)
                cliente = random.choice(clientes)
                quantidade = random.randint(1, 10)
                preco_total = quantidade * produto.sale_price
                lucro_total = quantidade * (produto.sale_price - produto.cost_price)
                data_venda = datetime.now() - timedelta(days=random.randint(0, 60))

                # Aleatoriza funcionário válido
                funcionario_id = None
                caixa_id = None

                if funcionarios and random.choice([True, False]):
                    funcionario = random.choice(funcionarios)
                    funcionario_id = funcionario.id

                    # Busca caixa aberto do funcionário
                    caixa = await CashController.get_caixa_aberto_funcionario(funcionario_id)
                    if caixa:
                        caixa_id = caixa.id

                forma_pagamento = random.choice(["PIX", "NOTA", "DINHEIRO", "CARTAO", "FIADO"])

                # Cria a venda
                venda = await Sales.create(
                    product_name=produto.name,
                    quantity=quantidade,
                    total_price=preco_total,
                    lucro_total=lucro_total,
                    cost_price=produto.cost_price,
                    criado_em=data_venda,
                    cliente_id=cliente.id,
                    usuario_id=admin.id,
                    funcionario_id=funcionario_id,
                    payment_method=forma_pagamento,
                    produto_id=produto.id,
                    sale_code=f"V{random.randint(10000, 99999)}",
                    caixa_id=caixa_id,  # ✅ Associa ao caixa
                )

                # Se a venda foi associada a um caixa, atualiza o saldo
                if caixa_id:
                    try:
                        await CashController.registrar_venda_caixa(
                            caixa_id=caixa_id, venda_id=venda.id, valor_venda=preco_total, forma_pagamento=forma_pagamento
                        )
                        print(f"✅ Venda {i+1} registrada no caixa {caixa_id}")
                    except Exception as e:
                        print(f"⚠️ Erro ao registrar venda no caixa: {e}")

                # Atualiza estoque
                produto.stock -= quantidade
                await produto.save()

            await barcode_generator(admin.id)
            await separating_sales_by_payments(admin.id)

            print("✅ 50 vendas criadas e estoque atualizado!")

        print("🎉 Dados mockados criados com sucesso!")
