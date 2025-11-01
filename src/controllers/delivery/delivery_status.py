# controller/delivery_status.py

from src.model.delivery import Delivery, DeliveryItem
from src.model.employee import Employees
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List


async def update_race_status(company_id: int) -> Dict[str, Any]:
    """
    update_race_status: Responsável por associar uma corrida a um entregador livre

    Esta função:
    - Busca corridas com status 'esperando' sem entregador atribuído
    - Encontra entregadores livres (sem entregas ativas)
    - Atribui automaticamente entregadores às corridas
    - Retorna relatório das atribuições realizadas

    Args:
        company_id (int): ID da empresa

    Returns:
        Dict[str, Any]: Relatório com atribuições realizadas e estatísticas
    """
    try:
        print(f"\n🔄 Iniciando atualização de status para empresa {company_id}")

        # Buscar corridas pendentes sem entregador
        corridas_pendentes = await Delivery.filter(usuario_id=company_id, delivery_status='esperando', assigned_to__isnull=True).all()

        if not corridas_pendentes:
            return {
                'success': True,
                'message': 'Nenhuma corrida pendente sem entregador atribuído',
                'atribuicoes_realizadas': 0,
                'corridas_pendentes': 0,
                'entregadores_disponiveis': 0,
            }

        print(f"📦 Encontradas {len(corridas_pendentes)} corridas pendentes")

        # Buscar entregadores ativos
        entregadores = await Employees.filter(usuario_id=company_id, cargo='Entregador', ativo=True).all()

        if not entregadores:
            return {
                'success': False,
                'error': 'Nenhum entregador ativo encontrado',
                'corridas_pendentes': len(corridas_pendentes),
                'entregadores_disponiveis': 0,
            }

        print(f"🚗 Encontrados {len(entregadores)} entregadores ativos")

        # Verificar quais entregadores estão livres
        entregadores_livres = []
        for entregador in entregadores:
            # Contar entregas ativas do entregador
            entregas_ativas = await Delivery.filter(
                usuario_id=company_id, assigned_to=entregador.nome, delivery_status__in=['esperando', 'em_andamento', 'a_caminho']
            ).count()

            if entregas_ativas == 0:
                entregadores_livres.append(entregador)
                print(f"   ✅ {entregador.nome} - LIVRE")
            else:
                print(f"   ⏳ {entregador.nome} - {entregas_ativas} entregas ativas")

        if not entregadores_livres:
            return {
                'success': False,
                'error': 'Nenhum entregador livre no momento',
                'corridas_pendentes': len(corridas_pendentes),
                'entregadores_ativos': len(entregadores),
                'entregadores_ocupados': len(entregadores),
            }

        print(f"🎯 {len(entregadores_livres)} entregadores livres disponíveis")

        # Ordenar corridas por prioridade (mais antigas primeiro)
        corridas_ordenadas = sorted(corridas_pendentes, key=lambda x: x.created_at)

        # Realizar atribuições
        atribuicoes_realizadas = []
        entregadores_atribuidos = set()

        for i, corrida in enumerate(corridas_ordenadas):
            if i >= len(entregadores_livres):
                break  # Não há mais entregadores disponíveis

            entregador = entregadores_livres[i]

            # Atribuir entregador à corrida
            corrida.assigned_to = entregador.nome
            await corrida.save()

            # Registrar atribuição
            atribuicoes_realizadas.append(
                {
                    'delivery_id': corrida.id,
                    'delivery_address': corrida.address,
                    'driver_id': entregador.id,
                    'driver_name': entregador.nome,
                    'assigned_at': datetime.now(timezone.utc).isoformat(),
                }
            )

            entregadores_atribuidos.add(entregador.id)

            print(f"   📍 Atribuído: {entregador.nome} → Corrida #{corrida.id}")

        # Estatísticas finais
        estatisticas = {
            'total_corridas_pendentes': len(corridas_pendentes),
            'total_entregadores_ativos': len(entregadores),
            'total_entregadores_livres': len(entregadores_livres),
            'atribuicoes_realizadas': len(atribuicoes_realizadas),
            'corridas_sem_entregador': len(corridas_pendentes) - len(atribuicoes_realizadas),
            'entregadores_nao_utilizados': len(entregadores_livres) - len(atribuicoes_realizadas),
        }

        return {
            'success': True,
            'message': f'Atribuições realizadas: {len(atribuicoes_realizadas)} corridas',
            'atribuicoes': atribuicoes_realizadas,
            'estatisticas': estatisticas,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        error_msg = f"Erro ao atualizar status das corridas: {str(e)}"
        print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'timestamp': datetime.now(timezone.utc).isoformat()}


async def assign_specific_delivery(delivery_id: int, driver_id: int, company_id: int) -> Dict[str, Any]:
    """
    Atribui uma corrida específica a um entregador específico

    Args:
        delivery_id (int): ID da corrida
        driver_id (int): ID do entregador
        company_id (int): ID da empresa

    Returns:
        Dict[str, Any]: Resultado da atribuição
    """
    try:
        # Verificar se a corrida existe e pertence à empresa
        corrida = await Delivery.filter(id=delivery_id, usuario_id=company_id).first()

        if not corrida:
            return {'success': False, 'error': f'Corrida #{delivery_id} não encontrada'}

        # Verificar se a corrida já tem entregador
        if corrida.assigned_to:
            return {'success': False, 'error': f'Corrida #{delivery_id} já está atribuída a {corrida.assigned_to}'}

        # Verificar se o entregador existe e é da empresa
        entregador = await Employees.filter(id=driver_id, usuario_id=company_id, cargo='Entregador', ativo=True).first()

        if not entregador:
            return {'success': False, 'error': f'Entregador #{driver_id} não encontrado ou inativo'}

        # Verificar se o entregador está livre
        entregas_ativas = await Delivery.filter(
            usuario_id=company_id, assigned_to=entregador.nome, delivery_status__in=['esperando', 'em_andamento', 'a_caminho']
        ).count()

        if entregas_ativas > 0:
            return {'success': False, 'error': f'Entregador {entregador.nome} já tem {entregas_ativas} entregas ativas'}

        # Realizar atribuição
        corrida.assigned_to = entregador.nome
        await corrida.save()

        return {
            'success': True,
            'message': f'Corrida #{delivery_id} atribuída a {entregador.nome}',
            'delivery_id': delivery_id,
            'driver_id': driver_id,
            'driver_name': entregador.nome,
            'assigned_at': datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        return {'success': False, 'error': f'Erro ao atribuir corrida: {str(e)}'}


async def get_delivery_status_report(company_id: int) -> Dict[str, Any]:
    """
    Gera relatório completo do status das entregas

    Args:
        company_id (int): ID da empresa

    Returns:
        Dict[str, Any]: Relatório detalhado das entregas
    """
    try:
        # Buscar todas as entregas da empresa
        todas_entregas = await Delivery.filter(usuario_id=company_id).all()

        # Estatísticas por status
        status_counts = {}
        for entrega in todas_entregas:
            status = entrega.delivery_status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Entregas sem entregador
        entregas_sem_entregador = await Delivery.filter(usuario_id=company_id, assigned_to__isnull=True, delivery_status='esperando').count()

        # Entregadores ativos
        entregadores_ativos = await Employees.filter(usuario_id=company_id, cargo='Entregador', ativo=True).count()

        # Entregadores ocupados
        entregadores_ocupados = (
            await Employees.filter(usuario_id=company_id)
            .annotate(entregas_ativas=Count(Delivery.filter(assigned_to=F('nome'), delivery_status__in=['esperando', 'em_andamento', 'a_caminho'])))
            .filter(entregas_ativas__gt=0)
            .count()
        )

        return {
            'success': True,
            'report': {
                'total_entregas': len(todas_entregas),
                'status_distribuicao': status_counts,
                'entregas_sem_entregador': entregas_sem_entregador,
                'entregadores_ativos': entregadores_ativos,
                'entregadores_ocupados': entregadores_ocupados,
                'entregadores_livres': entregadores_ativos - entregadores_ocupados,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            },
        }

    except Exception as e:
        return {'success': False, 'error': f'Erro ao gerar relatório: {str(e)}'}


async def update_payments_status(company_id: int, sales_id: int, new_status: str):
    """
    update_payments_status: Responsável por atualizar o status de pagamento de uma venda específica.

    Parâmetros:
    - company_id: ID da empresa (usuário)
    - sales_id: ID da venda (DeliveryItem)
    - new_status: Novo status de pagamento ('Pago', 'Receber na entrega', 'Pendente')
    """

    valid_statuses = ['Pago', 'Receber na entrega', 'Pendente']

    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status inválido. Os valores permitidos são: {valid_statuses}")

    # Busca o item de entrega específico
    delivery_item = await DeliveryItem.get_or_none(usuario_id=company_id, id=sales_id)

    if not delivery_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada para este usuário.")

    if delivery_item.payment_status == new_status:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "O status de pagamento já está atualizado."})

    # Atualiza o status de pagamento
    delivery_item.payment_status = new_status
    await delivery_item.save()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Status de pagamento atualizado com sucesso."})


async def total_sales(company_id: int):
    """
    total_sales: Responsável por calcular o total em reais de vendas no modo delivery.
    """

    # Busca todos os itens de entrega da empresa
    delivery_items = await DeliveryItem.filter(usuario_id=company_id).all()

    total = 0.0

    for item in delivery_items:
        total += item.quantity * item.price

    return {"total_em_reais": round(total, 2)}


async def sales_quantity(company_id: int):
    """
    sales_quantity: Responsável por exibir a quantidade de vendas realizadas no dia atual.
    """

    # Define o início e o fim do dia atual em UTC
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    # Filtra as entregas criadas hoje para o company_id
    vendas_do_dia = await Delivery.filter(usuario_id=company_id, created_at__gte=start_of_day, created_at__lt=end_of_day).count()

    return {"quantidade_vendas_hoje": vendas_do_dia}
