# src/conf/database.py
import os
from dotenv import load_dotenv
from tortoise import Tortoise
import asyncio

# Carregar variáveis de ambiente
load_dotenv()

# Dados de conexão — você pode mover para o .env se quiser
DB_USER = os.getenv("DB_USER", "naht1344_usuairos")
DB_PASS = os.getenv("DB_PASS", "3QzMZKGSGmJnchBd")
DB_HOST = os.getenv("DB_HOST", "localhost")  # ou o IP do servidor
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "naht1344_usuairos")

# Montar URL de conexão MySQL
mysql_url = f"mysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuração do Tortoise ORM
TORTOISE_ORM = {
    "connections": {"default": mysql_url},
    "apps": {
        "models": {
            "models": [
                "src.model.user",
                "src.model.employee",
                "src.model.customers",
                "src.model.caixa",
                "src.model.cashmovement",
                "src.model.sale",
                "src.model.partial",
                "src.model.carItems",
                "src.model.product",
                "src.model.fornecedor",
                "src.model.membros",
                "src.model.cnpjCache",
                "src.model.tickets",
                "src.model.delivery",
                "src.model.pix",
            ],
            "default_connection": "default",
        }
    },
}


async def print_database_info():
    """Função para imprimir informações do banco de dados"""
    try:
        print("\n" + "=" * 80)
        print("📊 DEBUG - DADOS DO BANCO DE DADOS")
        print("=" * 80)

        # Conectar ao banco
        await Tortoise.init(config=TORTOISE_ORM)

        # PRIMEIRO: Descobrir quais tabelas existem
        print("\n🔍 TABELAS EXISTENTES NO BANCO:")
        print("-" * 50)
        tabelas = await Tortoise.get_connection("default").execute_query("SHOW TABLES")
        for tabela in tabelas[1]:
            table_name = list(tabela.values())[0]
            print(f"📋 {table_name}")

        # 1. USUÁRIOS/EMPRESAS - Tentar diferentes nomes de tabela
        print("\n👥 TABELA: USUARIOS/EMPRESAS")
        print("-" * 50)

        # Tentar diferentes nomes possíveis para a tabela de usuários
        tabelas_usuarios = ['usuarios', 'user', 'users', 'usuario', 'empresas', 'companies']
        usuarios_encontrados = None

        for tabela in tabelas_usuarios:
            try:
                usuarios = await Tortoise.get_connection("default").execute_query(f"SELECT * FROM {tabela} ORDER BY id")
                if usuarios[1]:
                    print(f"✅ Tabela encontrada: {tabela}")
                    usuarios_encontrados = usuarios[1]
                    break
            except:
                continue

        if usuarios_encontrados:
            for user in usuarios_encontrados:
                print(
                    f"ID: {user.get('id')} | Nome: {user.get('username', user.get('name', 'N/A'))} | Email: {user.get('email', 'N/A')} | Empresa: {user.get('company_name', user.get('name', 'N/A'))}"
                )
        else:
            print("❌ Nenhuma tabela de usuários encontrada")

        # 2. FUNCIONÁRIOS - Tentar diferentes nomes
        print("\n👨‍💼 TABELA: FUNCIONÁRIOS")
        print("-" * 50)

        tabelas_funcionarios = ['employees', 'employee', 'funcionarios', 'funcionario']
        funcionarios_encontrados = None

        for tabela in tabelas_funcionarios:
            try:
                funcionarios = await Tortoise.get_connection("default").execute_query(f"SELECT * FROM {tabela} ORDER BY id")
                if funcionarios[1]:
                    print(f"✅ Tabela encontrada: {tabela}")
                    funcionarios_encontrados = funcionarios[1]
                    break
            except:
                continue

        if funcionarios_encontrados:
            for func in funcionarios_encontrados:
                print(
                    f"ID: {func.get('id')} | Nome: {func.get('name', func.get('nome', 'N/A'))} | Email: {func.get('email', 'N/A')} | User ID: {func.get('usuario_id', func.get('user_id', 'N/A'))}"
                )
        else:
            print("❌ Nenhuma tabela de funcionários encontrada")

        # 3. CAIXAS - Tentar diferentes nomes
        print("\n💰 TABELA: CAIXA")
        print("-" * 50)

        tabelas_caixa = ['caixa', 'caixas', 'cash', 'cash_register']
        caixas_encontrados = None

        for tabela in tabelas_caixa:
            try:
                caixas = await Tortoise.get_connection("default").execute_query(f"SELECT * FROM {tabela} ORDER BY id DESC LIMIT 10")
                if caixas[1]:
                    print(f"✅ Tabela encontrada: {tabela}")
                    caixas_encontrados = caixas[1]
                    break
            except:
                continue

        if caixas_encontrados:
            for caixa in caixas_encontrados:
                status = "✅ ABERTO" if caixa.get('aberto') else "❌ FECHADO"
                print(
                    f"ID: {caixa.get('id')} | Nome: {caixa.get('nome', 'N/A')} | User ID: {caixa.get('usuario_id')} | Func ID: {caixa.get('funcionario_id')} | {status} | Saldo: R$ {caixa.get('saldo_atual', 0)}"
                )
        else:
            print("❌ Nenhuma tabela de caixa encontrada")

        # 4. VERIFICAÇÃO ESPECÍFICA DO PROBLEMA
        print("\n🔍 VERIFICAÇÃO ESPECÍFICA DO PROBLEMA")
        print("-" * 50)

        if funcionarios_encontrados and usuarios_encontrados:
            # Encontrar funcionário ID 2
            func_2 = None
            for func in funcionarios_encontrados:
                if func.get('id') == 2:
                    func_2 = func
                    break

            if func_2:
                user_id_func = func_2.get('usuario_id', func_2.get('user_id'))
                print(f"🔎 Funcionário ID 2:")
                print(f"   • Nome: {func_2.get('name', 'N/A')}")
                print(f"   • Pertence ao User ID: {user_id_func}")

                # Verificar se esse user_id existe na tabela de usuários
                user_existe = False
                for user in usuarios_encontrados:
                    if user.get('id') == user_id_func:
                        user_existe = True
                        print(f"   • ✅ User ID {user_id_func} existe: {user.get('username', 'N/A')} - {user.get('company_name', 'N/A')}")
                        break

                if not user_existe:
                    print(f"   • ❌ User ID {user_id_func} NÃO ENCONTRADO na tabela de usuários!")
            else:
                print("❌ Funcionário ID 2 não encontrado")
        else:
            print("❌ Não foi possível fazer a verificação - tabelas necessárias não encontradas")

        print("\n" + "=" * 80)
        print("✅ DEBUG COMPLETO")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Erro ao acessar banco de dados: {e}")
        import traceback

        print(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        await Tortoise.close_connections()
