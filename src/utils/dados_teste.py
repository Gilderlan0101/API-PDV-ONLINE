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
from src.controllers.payments.partial import PartialPayment
from src.utils.sales_code_generator import lot_bar_code_size

__PAYMENT_METHODS = ['PIX', 'CARTAO', 'DINHEIRO']


async def create_mock_data():
    """Cria usuário admin, funcionários, clientes e produtos de teste (mínimo necessário)."""
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
            admin_2 = await Usuario.create(
                username="admin",
                email="admin_2@test.com",
                password=get_hashed_password("123456"),
                company_name="Empresa Teste 1",
                trade_name="Loja Central",
                membros=1,
                cnpj="12245678000199",
                city="São Paulo",
                state="SP",
                pending=True,
            )
            admin_3 = await Usuario.create(
                username="admin",
                email="admin_3@test.com",
                password=get_hashed_password("123456"),
                company_name="Empresa Teste 1",
                trade_name="Loja Central",
                membros=1,
                cnpj="12345678000199",
                city="São Paulo",
                state="SP",
                is_active=False,
            )
            await Membro.create(
                nome="Filial Centro",
                email="membro@test.com",
                senha=get_hashed_password("1234"),
                ativo=True,
                gerente="João",
                usuario_id=admin.id,
            )
            print(f"✅ Usuário admin criado: {admin.email}")

        # ========================
        # Criar funcionários (fixos)
        # ========================
        funcionarios_emails = ["gilderlan@teste.com", "maria@teste.com", "gilvan@teste.com"]
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

        # ========================
        # Criar produtos (10 fixos)
        # ========================
        produtos_data = [
            {"code": "PROD001", "name": "Coca-Cola 2L", "cost": 5.50, "sale": 8.00, "supplier": "Coca-Cola"},
            {"code": "PROD002", "name": "Suco de Laranja 1L", "cost": 4.00, "sale": 6.50, "supplier": "Del Valle"},
            {"code": "PROD003", "name": "Água Mineral 500ml", "cost": 1.00, "sale": 2.50, "supplier": "Crystal"},
            {"code": "PROD004", "name": "Cerveja Heineken 600ml", "cost": 6.00, "sale": 9.00, "supplier": "Heineken"},
            {"code": "PROD005", "name": "Energético Red Bull", "cost": 7.50, "sale": 12.00, "supplier": "Red Bull"},
            {"code": "PROD006", "name": "Arroz 5kg", "cost": 18.00, "sale": 25.00, "supplier": "Tio João"},
            {"code": "PROD007", "name": "Feijão 1kg", "cost": 8.00, "sale": 12.00, "supplier": "Camil"},
            {"code": "PROD008", "name": "Óleo de Soja 900ml", "cost": 5.00, "sale": 8.00, "supplier": "Liza"},
            {"code": "PROD009", "name": "Macarrão Espaguete 500g", "cost": 3.50, "sale": 6.00, "supplier": "Renata"},
            {"code": "PROD010", "name": "Detergente 500ml", "cost": 1.50, "sale": 3.00, "supplier": "Ypê"},
        ]

        tickets = [
            {"ticket": "Novo"},
            {"ticket": "Promoção"},
            {"ticket": "Ofertas"},
            {"ticket": "Destaques"},
        ]

        for p in produtos_data:
            for ticket in tickets:
                produto = await Produto.filter(product_code=p["code"], usuario_id=admin.id).first()
                if not produto:
                    ticket = random.choice([t["ticket"] for t in tickets])
                    await Produto.create(
                        product_code=p["code"],
                        name=p["name"],
                        stock=10,
                        stoke_max=300,
                        stoke_min=20,
                        cost_price=p["cost"],
                        price_uni=p["cost"] * 1.2,
                        sale_price=p["sale"],
                        supplier=p["supplier"],
                        ticket=ticket,
                        controllstoke=random.choice(["Sim", "Não"]),
                        group=random.choice(['Bebidas', 'Gelados', 'Brinquedos']),
                        usuario_id=admin.id,
                    )
                    print(f"✅ Produto criado: {p['name']}")

        # ========================
        # Criar clientes (3 ativos)
        # ========================
        clientes_nomes = ["João Silva", "Maria Souza", "Carlos Pereira"]
        for nome in clientes_nomes:
            cliente = await Customer.filter(full_name=nome, usuario_id=admin.id).first()
            if not cliente:
                cpf_numbers_only = re.sub(r"\D", "", fake.cpf())
                await Customer.create(
                    full_name=nome,
                    birth_date=fake.date_of_birth(minimum_age=18, maximum_age=60).isoformat(),
                    cpf=cpf_numbers_only,
                    mother_name=fake.name_female(),
                    road=fake.street_name(),
                    house_number=123,
                    neighborhood=fake.bairro(),
                    city=fake.city(),
                    tel=fake.cellphone_number(),
                    cep=fake.postcode(),
                    credit=500.00,
                    current_balance=0.00,
                    due_date=datetime.now(),
                    status="ATIVO",
                    usuario_id=admin.id,
                )
                print(f"✅ Cliente criado: {nome}")

        # Cadastrado uma venda no formato de pagamento parcial
        # Onde o objetivo e recebe um um valor ate que a divida seja fechada

        import json

        names = ['Gilderlan', 'maria', 'otavio', 'mainco', 'jessica']
        cpfs = [123456789098, 123454439098, 123256739098, 43645298723383, 103456789098]
        tels = [1234567891234, 13456732156754, 398765432121, 83645298710983, 98876547658767]

        for name, cpf, tel in zip(names, cpfs, tels):
            partial = await Partial.filter(customers_name=name, usuario_id=admin.id).first()
            if not partial:

                await Partial.create(
                    usuario_id=admin.id,
                    customers_name=name,
                    cpf=str(cpf),  # pega 1 CPF
                    tel=str(tel),  # pega 1 telefone
                    product_name=random.choice(produtos_data).get("name"),
                    value=100.00,
                    payment_method=random.choice(__PAYMENT_METHODS),
                    date=datetime.now(),
                )

        cliente_teste = await Partial.first()

        if cliente_teste:
            # Criando a instância da classe
            teste_venda_parcial = PartialPayment(
                payment_method=cliente_teste.payment_method,
                value_received=50,  # pagando metade
                cpf=cliente_teste.cpf,
                user_id=cliente_teste.usuario_id,
            )

            # Rodando a atualização
            resultado = await teste_venda_parcial.update_value()
            print("Dados de cliente atualizado")

        print("🎉 Dados de teste criados com sucesso (mínimos necessários)!")
