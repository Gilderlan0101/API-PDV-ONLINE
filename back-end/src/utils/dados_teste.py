from sqlmodel import Session, select
from datetime import datetime
from zoneinfo import ZoneInfo
from passlib.hash import bcrypt  # Se você usar bcrypt para senhas
from ..model.user.users import Usuario, Membro, Produto
from ..conf.database import engine


def create_mock_data():
    """Cria usuários, filiais e produtos de teste se não existirem."""
    with Session(engine) as session:
        # ========================
        # Criar usuários de teste
        # ========================
        if not session.exec(select(Usuario)).first():
            print('🔹 Criando usuários de teste...')

            user1 = Usuario(
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

            user2 = Usuario(
                username='user2',
                email='user2@test.com',
                password=bcrypt.hash('123456'),
                company_name='Empresa Teste 2',
                trade_name='Filial Norte',
                membros=1,
                cnpj='98765432000188',
                city='Rio de Janeiro',
                state='RJ',
            )

            session.add(user1)
            session.add(user2)
            session.commit()
            session.refresh(user1)
            session.refresh(user2)

            print('✅ Usuários criados:', user1.email, user2.email)

            # ========================
            # Criar filiais
            # ========================
            branch1 = Membro(
                nome='Filial Centro',
                gerente='João',
                usuario_id=user1.id,  # type: ignore
            )
            branch2 = Membro(
                nome='Filial Zona Sul',
                gerente='Maria',
                usuario_id=user2.id,  # type: ignore
            )

            session.add(branch1)
            session.add(branch2)
            session.commit()

            # ========================
            # Criar produtos de teste
            # ========================
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
                    usuario_id=user1.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD002',
                    name='Arroz Branco 5kg',
                    stock=100,
                    cost_price=15.00,
                    price_uni=18.00,
                    sale_price=20.00,
                    supplier='Camil',
                    usuario_id=user1.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD003',
                    name='Detergente Neutro 500ml',
                    stock=200,
                    cost_price=1.00,
                    price_uni=1.50,
                    sale_price=2.00,
                    supplier='Limpeza BR',
                    usuario_id=user2.id,  # type: ignore
                ),
                Produto(
                    product_code='PROD004',
                    name='Lata 350ml',
                    stock=10,
                    stoke_max=300,
                    stoke_min=50,
                    cost_price=2.50,
                    price_uni=3.50,
                    sale_price=4.00,
                    supplier='Distribuidora Bebidas',
                    usuario_id=user1.id,  # type: ignore
                ),
            ]

            session.add_all(products)
            session.commit()
            print('✅ Produtos de teste criados!')
        else:
            print('⚡ Dados de teste já existem. Nenhuma ação feita.')
