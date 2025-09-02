from tortoise import Tortoise, run_async
from src.model.user import Usuario
from src.model.employee import Employees
import os

DB_PATH = "/home/dev/projetos/API-PDV-ONLINE/back-end/usurios.db"

async def debug_usuarios_funcionarios():
    """Função para debug que lista todos os usuários e seus funcionários"""

    print("=" * 60)
    print("DEBUG: LISTA DE USUÁRIOS E FUNCIONÁRIOS")
    print("=" * 60)

    # Inicializa conexão com o banco SQLite existente
    await Tortoise.init(
        db_url=f"sqlite://{DB_PATH}",
        modules={"models": ["src.model.user", "src.model.employee"]},
    )
    # NÃO gera schemas se o banco já existe
    # await Tortoise.generate_schemas()

    # Busca todos os usuários
    usuarios = await Usuario.all()
    
    for usuario in usuarios:
        print(f"\n📋 USUÁRIO: ID={usuario.id}, Username='{usuario.username}', Email='{usuario.email}'")
        print(f"   Company: '{usuario.company_name}', CNPJ: {usuario.cnpj}")
        
        # Busca funcionários deste usuário
        funcionarios = await Employees.filter(usuario_id=usuario.id).all()
        
        if funcionarios:
            print(f"   👥 FUNCIONÁRIOS ({len(funcionarios)}):")
            for func in funcionarios:
                print(f"      - ID: {func.id}, Nome: '{func.nome}', Cargo: '{func.cargo}', Email: '{func.email}'")
                print(f"        Ativo: {func.ativo}, Criado em: {func.criado_em}")
        else:
            print(f"   ❌ NENHUM FUNCIONÁRIO CADASTRADO PARA ESTE USUÁRIO")
    
    print("=" * 60)
    print("DEBUG COMPLETO")
    print("=" * 60)

    # Fecha conexões ao final
    await Tortoise.close_connections()

# Executa a função
if __name__ == "__main__":
    run_async(debug_usuarios_funcionarios())
