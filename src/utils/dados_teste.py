from passlib.hash import bcrypt
from datetime import datetime, timedelta
import random
from faker import Faker
from src.model.product import Produto
from src.model.user import Membro, Usuario
from src.model.customers import Customer
from src.model.sale import Sales
from src.model.employee import Employees
from tortoise.transactions import in_transaction
import re

async def create_mock_data():
    """Cria usuário admin, produtos, clientes e vendas mockadas."""
    fake = Faker('pt_BR')

    async with in_transaction() as conn:
        # ========================
        # Criar usuário admin
        # ========================
        admin = await Usuario.filter(email="admin@test.com").first()
        if not admin:
            print('🔹 Criando usuário admin...')
            admin = await Usuario.create(
                username='admin',
                email='admin@test.com',
                password=bcrypt.hash('123456'),
                company_name='Empresa Teste 1',
                trade_name='Loja Central',
                membros=1,
                cnpj='12345678000199',
                city='São Paulo',
                state='SP'
            )

            # Criar filial padrão
            await Membro.create(
                nome='Filial Centro',
                gerente='João',
                usuario_id=admin.id,
            )

            print(f'✅ Usuário admin criado: {admin.email}')

        # ========================
        # Criar funcionário padrão
        # ========================
        funcionario = await Employees.filter(usuario_id=admin.id).first()
        if not funcionario:
            funcionario = await Employees.create(
                nome="Funcionário Padrão",
                cargo="Caixa",
                usuario_id=admin.id
            )
            print(f'✅ Funcionário criado: {funcionario.nome}')

        # ========================
        # Criar 20 produtos diferentes
        # ========================
        produtos_existentes = await Produto.filter(usuario_id=admin.id).all()
        if len(produtos_existentes) < 20:
            print('🔹 Criando 20 produtos diferentes...')
            produtos_data = [
                # Bebidas
                {'code': 'BEB001', 'name': 'Coca-Cola 2L', 'cost': 5.50, 'sale': 8.00, 'supplier': 'Coca-Cola'},
                {'code': 'BEB002', 'name': 'Suco de Laranja 1L', 'cost': 4.00, 'sale': 6.50, 'supplier': 'Del Valle'},
                {'code': 'BEB003', 'name': 'Água Mineral 500ml', 'cost': 1.00, 'sale': 2.50, 'supplier': 'Crystal'},
                {'code': 'BEB004', 'name': 'Cerveja Heineken 600ml', 'cost': 6.00, 'sale': 9.00, 'supplier': 'Heineken'},
                {'code': 'BEB005', 'name': 'Energético Red Bull', 'cost': 7.50, 'sale': 12.00, 'supplier': 'Red Bull'},
                # Alimentos
                {'code': 'ALI001', 'name': 'Arroz 5kg', 'cost': 18.00, 'sale': 25.00, 'supplier': 'Tio João'},
                {'code': 'ALI002', 'name': 'Feijão 1kg', 'cost': 8.00, 'sale': 12.00, 'supplier': 'Camil'},
                {'code': 'ALI003', 'name': 'Açúcar 5kg', 'cost': 12.00, 'sale': 18.00, 'supplier': 'União'},
                {'code': 'ALI004', 'name': 'Óleo de Soja 900ml', 'cost': 5.00, 'sale': 8.00, 'supplier': 'Liza'},
                {'code': 'ALI005', 'name': 'Macarrão Espaguete 500g', 'cost': 3.50, 'sale': 6.00, 'supplier': 'Renata'},
                # Limpeza
                {'code': 'LIM001', 'name': 'Detergente 500ml', 'cost': 1.50, 'sale': 3.00, 'supplier': 'Ypê'},
                {'code': 'LIM002', 'name': 'Sabão em Pó 1kg', 'cost': 8.00, 'sale': 12.00, 'supplier': 'OMO'},
                {'code': 'LIM003', 'name': 'Amaciante 2L', 'cost': 9.00, 'sale': 15.00, 'supplier': 'Comfort'},
                {'code': 'LIM004', 'name': 'Desinfetante 1L', 'cost': 4.50, 'sale': 7.50, 'supplier': 'Pinho Sol'},
                {'code': 'LIM005', 'name': 'Esponja de Aço', 'cost': 0.80, 'sale': 2.00, 'supplier': 'Bombril'},
                # Higiene
                {'code': 'HIG001', 'name': 'Pasta de Dente 90g', 'cost': 3.00, 'sale': 5.50, 'supplier': 'Colgate'},
                {'code': 'HIG002', 'name': 'Sabonete 90g', 'cost': 1.20, 'sale': 2.50, 'supplier': 'Dove'},
                {'code': 'HIG003', 'name': 'Shampoo 350ml', 'cost': 8.00, 'sale': 14.00, 'supplier': 'Head & Shoulders'},
                {'code': 'HIG004', 'name': 'Papel Higiênico 4un', 'cost': 4.00, 'sale': 7.00, 'supplier': 'Neve'},
                {'code': 'HIG005', 'name': 'Fio Dental 50m', 'cost': 2.50, 'sale': 4.50, 'supplier': 'Oral-B'}
            ]

            for prod_data in produtos_data:
                await Produto.create(
                    product_code=prod_data['code'],
                    name=prod_data['name'],
                    stock=random.randint(50, 200),
                    stoke_max=300,
                    stoke_min=20,
                    cost_price=prod_data['cost'],
                    price_uni=prod_data['cost'] * 1.2,
                    sale_price=prod_data['sale'],
                    supplier=prod_data['supplier'],
                    usuario_id=admin.id
                )
            print('✅ 20 produtos criados!')
        else:
            print(f'⚡ Já existem {len(produtos_existentes)} produtos. Nenhuma ação feita.')

        # ========================
        # Criar 30 clientes diferentes
        # ========================
        clientes_existentes = await Customer.filter(usuario_id=admin.id).all()
        if len(clientes_existentes) < 30:
            print('🔹 Criando 30 clientes diferentes...')
            for _ in range(30):
                cpf_numbers_only = re.sub(r'\D', '', fake.cpf())  # ✅ apenas números
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
                    status="ATIVO",
                    usuario_id=admin.id
                )
            print('✅ 30 clientes criados!')
        else:
            print(f'⚡ Já existem {len(clientes_existentes)} clientes. Nenhuma ação feita.')

        # ========================
        # Criar 50 vendas mockadas
        # ========================
        vendas_existentes = await Sales.filter(usuario_id=admin.id).all()
        if len(vendas_existentes) < 50:
            print('🔹 Criando 50 vendas mockadas...')
            produtos = await Produto.filter(usuario_id=admin.id).all()
            clientes = await Customer.filter(usuario_id=admin.id).all()
            if not produtos or not clientes:
                print('❌ É necessário ter produtos e clientes para criar vendas!')
                return

            for _ in range(50):
                produto = random.choice(produtos)
                cliente = random.choice(clientes)
                quantidade = random.randint(1, 10)
                preco_total = quantidade * produto.sale_price
                lucro_total = quantidade * (produto.sale_price - produto.cost_price)
                data_venda = datetime.now() - timedelta(days=random.randint(0, 60))

                venda = await Sales.create(
                    product_name=produto.name,
                    quantity=quantidade,
                    total_price=preco_total,
                    lucro_total=lucro_total,
                    cost_price=produto.cost_price,
                    criado_em=data_venda,
                    cliente_id=cliente.id,
                    usuario_id=admin.id,
                    funcionario_id=funcionario.id,  # ✅ corrigido
                    produto_id=produto.id,
                    codigo_da_venda=f"V{random.randint(10000, 99999)}"
                )

                # Atualizar estoque do produto
                produto.stock -= quantidade
                await produto.save()

            print('✅ 50 vendas criadas e estoque atualizado!')
        else:
            print(f'⚡ Já existem {len(vendas_existentes)} vendas. Nenhuma ação feita.')

        print('🎉 Dados mockados criados com sucesso!')
