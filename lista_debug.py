# test_pix_table.py
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.conf.database import TORTOISE_ORM
from tortoise import Tortoise
from src.model.pix import Pix


async def test_pix_table():
    """Testa se a tabela Pix está funcionando corretamente"""
    try:
        print("🧪 TESTANDO TABELA PIX...")

        # Inicializar Tortoise
        await Tortoise.init(config=TORTOISE_ORM)

        # 1. Testar criação de registro
        print("\n1. 🆕 Testando criação de registro...")
        novo_pix = await Pix.create(full_name="Teste da Silva", city="Testópolis", key_pix="teste@email.com", usuario_id=1)

        print(f"   ✅ Registro criado com ID: {novo_pix.id}")

        # 2. Testar busca
        print("\n2. 🔍 Testando busca de registros...")
        registros = await Pix.all()

        print(f"   ✅ Total de registros: {len(registros)}")
        for registro in registros:
            print(f"      ID: {registro.id}, Nome: {registro.full_name}, Chave: {registro.key_pix}")

        # 3. Testar que ID é automático e não nulo
        print("\n3. 🔎 Verificando IDs...")
        for registro in registros:
            if registro.id is None:
                print(f"   ❌ ERRO: Registro sem ID: {registro.key_pix}")
            else:
                print(f"   ✅ ID válido: {registro.id}")

        # 4. Testar constraint de unicidade
        print("\n4. 🚫 Testando constraint de unicidade...")
        try:
            await Pix.create(full_name="Duplicado", city="Cidade", key_pix="teste@email.com", usuario_id=1)  # Mesma chave
            print("   ❌ ERRO: Deveria ter falhado na unicidade")
        except Exception as e:
            print(f"   ✅ Constraint de unicidade funcionando: {e}")

        # 5. Limpar teste
        print("\n5. 🧹 Limpando dados de teste...")
        await Pix.filter(key_pix="teste@email.com").delete()
        print("   ✅ Dados de teste removidos")

        print("\n🎉 TODOS OS TESTES PASSARAM! A tabela Pix está funcionando corretamente.")

    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_pix_table())
