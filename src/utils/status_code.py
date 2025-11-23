# migration_caixa_final_simples.py
import asyncio
import random

from tortoise import Tortoise, run_async

from src.conf.database import TORTOISE_ORM


async def migrate_caixa_final():
    """Migração simplificada - apenas popula caixa_id"""
    await Tortoise.init(config=TORTOISE_ORM)

    try:
        from src.model.caixa import Caixa

        print('🔄 Iniciando migração de caixa_id...')

        # Busca caixas sem caixa_id
        caixas_sem_id = await Caixa.filter(
            caixa_id__isnull=True
        ).prefetch_related('usuario', 'funcionario')

        print(f'📦 Caixas sem ID: {len(caixas_sem_id)}')

        if len(caixas_sem_id) == 0:
            print('✅ Todos os caixas já têm ID!')
            return

        # Processa por empresa
        caixas_por_empresa = {}
        for caixa in caixas_sem_id:
            if caixa.usuario_id not in caixas_por_empresa:
                caixas_por_empresa[caixa.usuario_id] = []
            caixas_por_empresa[caixa.usuario_id].append(caixa)

        total_atualizados = 0

        for empresa_id, caixas in caixas_por_empresa.items():
            print(f'\n🏢 Empresa {empresa_id}: {len(caixas)} caixas sem ID')

            # Pega IDs já em uso por esta empresa
            caixas_existentes = await Caixa.filter(
                usuario_id=empresa_id, caixa_id__isnull=False
            )
            ids_em_uso = set(c.caixa_id for c in caixas_existentes)

            for caixa in caixas:
                # Gera ID único para esta empresa
                novo_id = random.randint(100, 999)
                tentativas = 0

                while novo_id in ids_em_uso and tentativas < 50:
                    novo_id = random.randint(100, 999)
                    tentativas += 1

                if tentativas >= 50:
                    # Fallback: usa ID do caixa + offset
                    novo_id = 1000 + caixa.id

                caixa.caixa_id = novo_id
                ids_em_uso.add(novo_id)
                await caixa.save()
                total_atualizados += 1

                funcionario_nome = (
                    caixa.funcionario.nome
                    if caixa.funcionario
                    else 'Sem funcionário'
                )
                print(f'  ✅ {funcionario_nome} -> ID: {caixa.caixa_id}')

        print(
            f'\n✅ Migração concluída! {total_atualizados} caixas atualizados.'
        )

        # Verificação rápida
        caixas_sem_id_final = await Caixa.filter(caixa_id__isnull=True).count()
        print(f'📊 Caixas ainda sem ID: {caixas_sem_id_final}')

    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback

        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == '__main__':
    run_async(migrate_caixa_final())
