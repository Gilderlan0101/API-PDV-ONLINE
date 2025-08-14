from passlib.hash import bcrypt
from sqlmodel import Session, select

from src.model.product import Produto

from ..conf.database import engine
from ..model.user import Membro, Usuario


def create_mock_data():
    """Cria usuário admin e 5 produtos de teste para ele se não existirem."""
    with Session(engine) as session:
        # ========================
        # Criar usuário admin
        # ========================
        admin = session.exec(
            select(Usuario).where(Usuario.email == "admin@test.com")
        ).first()
        if not admin:
            print('🔹 Criando usuário admin...')

            admin = Usuario(
                username='admin',
                email='admin@test.com',
                password=bcrypt.hash('123456'),
                company_name='Empresa Teste 1',
                trade_name='Loja Central',
                membros=1,
                cnpj='12345678000199',
                city='São Paulo',
                state='SP',
            )

            session.add(admin)
            session.commit()
            session.refresh(admin)

            # Criar filial padrão
            branch = Membro(
                nome='Filial Centro',
                gerente='João',
                usuario_id=admin.id,  # type: ignore
            )
            session.add(branch)
            session.commit()

            print(f'✅ Usuário admin criado: {admin.email}')

        # ========================
        # Criar produtos para o admin
        # ========================
        produtos_existentes = session.exec(
            select(Produto).where(Produto.usuario_id == admin.id)  # type: ignore
        ).all()

        if not produtos_existentes:
            print('🔹 Criando produtos de teste para admin...')

            products = [
                Produto(
                    product_code='PROD001',
                    name='Coca-Cola Lata 350ml',
                    stock=10,
                    stoke_max=300,
                    stoke_min=50,
                    cost_price=2.50,
                    price_uni=3.50,
                    sale_price=4.00,
                    supplier='Distribuidora Bebidas',
                    usuario_id=admin.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD002',
                    name='Arroz Branco 5kg',
                    stock=100,
                    cost_price=15.00,
                    price_uni=18.00,
                    sale_price=20.00,
                    supplier='Camil',
                    usuario_id=admin.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD003',
                    name='Detergente Neutro 500ml',
                    stock=200,
                    cost_price=1.00,
                    price_uni=1.50,
                    sale_price=2.00,
                    supplier='Limpeza BR',
                    usuario_id=admin.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD004',
                    name='Biscoito Cream Cracker 400g',
                    stock=50,
                    cost_price=3.00,
                    price_uni=4.00,
                    sale_price=5.00,
                    supplier='Mabel',
                    usuario_id=admin.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD005',
                    name='Leite Integral 1L',
                    stock=80,
                    cost_price=4.20,
                    price_uni=5.00,
                    sale_price=6.00,
                    supplier='Italac',
                    usuario_id=admin.id,  # type: ignore
                ),
            ]

            session.add_all(products)
            session.commit()
            print('✅ Produtos de teste criados para admin!')
        else:
            print('⚡ Produtos para admin já existem. Nenhuma ação feita.')
