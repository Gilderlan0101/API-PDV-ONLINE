# src/controllers/cash_controller.py
from tortoise.transactions import in_transaction
from datetime import datetime
from zoneinfo import ZoneInfo
from src.model.cashmovement import CashMovement
from src.model.caixa import Caixa
from src.model.user import Usuario
from src.model.employee import Employees

from typing import Dict, Any
from src.model.caixa import Caixa
from src.model.sale import Sales


from src.controllers.sales.sales import Checkout

class CashController:

    @staticmethod
    async def abrir_caixa(funcionario_id: int, saldo_inicial: float, nome: str):
        """
        Abre um novo caixa para um funcionário, garantindo que só um fique aberto
        """
        # Verifica se o usuário existe
        # usuario_exists = await Employees.exists(id=usuario_id)
        # if not usuario_exists:
        #     raise Exception("Usuário não encontrado")
        
        # Verifica se o funcionário existe
        funcionario = await Employees.filter(id=funcionario_id).first()
        if not funcionario:
            raise Exception("Funcionário não encontrado")
        
        # Busca todos os caixas abertos do funcionário
        caixas_abertos = await Caixa.filter(funcionario_id=funcionario_id, aberto=True).all()
        
        # if caixas_abertos:
        #     # Fecha todos os caixas existentes (mantém só o primeiro)
        #     for caixa in caixas_abertos[1:]:
        #         caixa.aberto = False
        #         await caixa.save()

            # Usa o primeiro caixa aberto como o "oficial"
            return caixas_abertos
        
        # Pegando o nome do fucionario
        if not nome:
            nome = funcionario.nome

        # Buscar o usuario dono do fucionario: usuario_id
        usuario_id =  funcionario.usuario_id
        
        # Se não tinha nenhum aberto, cria novo caixa
        caixa = await Caixa.create(
            nome=nome,
            saldo_inicial=saldo_inicial,
            saldo_atual=saldo_inicial,
            aberto=True,
            usuario_id=usuario_id,
            funcionario_id=funcionario_id,
        )

        # Registra movimentação de abertura
        await CashMovement.create(
            tipo="ABERTURA",
            valor=saldo_inicial,
            descricao=f"Abertura do caixa {nome}",
            caixa_id=caixa.id,
            usuario_id=usuario_id,
            funcionario_id=funcionario_id,
        )

        return caixa



    @staticmethod
    async def registrar_venda_caixa(caixa_id: int, venda_obj: Sales, valor_venda: float, forma_pagamento: str):
        caixa = await Caixa.get_or_none(id=caixa_id)
        if not caixa or not caixa.aberto:
            raise Exception("Caixa não encontrado ou fechado")

        # Verifica se venda_obj é realmente uma instância de Sales
        if not isinstance(venda_obj, Sales):
            raise Exception(f"Objeto de venda inválido: {type(venda_obj)}")

        caixa.saldo_atual += valor_venda

        # Registra movimentação - CORRIGIDO: passar a instância completa de Sales
        await CashMovement.create(
            tipo="ENTRADA",
            valor=valor_venda,
            descricao=f"Venda #{venda_obj.id} - {forma_pagamento}",
            caixa=caixa,  # Passar instância do caixa
            usuario=caixa.usuario,  # Passar instância do usuário
            funcionario=caixa.funcionario,  # Passar instância do funcionário (pode ser None)
            venda=venda_obj,  # CORREÇÃO: passar a instância completa de Sales
        )

        await caixa.save()
        return caixa



    @staticmethod
    async def fechar_caixa(usuario_id: int):
        """
        Fecha o caixa aberto do usuário e calcula as diferenças
        """
        date = []

        # 🔹 Busca o caixa aberto do usuário
        caixa = await Caixa.filter(funcionario_id=usuario_id, aberto=True).first()

        if not caixa:
            return None  # nenhum caixa aberto encontrado

        # Calcula entradas e saídas
        entradas = await CashMovement.filter(
            caixa_id=caixa.id,
            tipo__in=["ENTRADA", "ABERTURA"]
        ).all()

        saidas = await CashMovement.filter(
            caixa_id=caixa.id,
            tipo="SAIDA"
        ).all()

        total_entradas = sum([mov.valor for mov in entradas])
        total_saidas = sum([mov.valor for mov in saidas])
        valor_sistema = total_entradas - total_saidas
        valor_fechamento = caixa.saldo_atual

        # Atualiza caixa
        caixa.valor_fechamento = valor_fechamento
        caixa.valor_sistema = valor_sistema
        caixa.diferenca = valor_fechamento - valor_sistema
        caixa.aberto = False
        caixa.atualizado_em = datetime.now(ZoneInfo("America/Sao_Paulo"))
        await caixa.save()

        # Registra movimentação
        await CashMovement.create(
            tipo="FECHAMENTO",
            valor=valor_fechamento,
            descricao=(
                f"Fechamento do caixa - Sistema: {valor_sistema}, "
                f"Fechamento: {valor_fechamento}, Dif: {caixa.diferenca}"
            ),
            caixa_id=caixa.id,
            usuario_id=caixa.usuario_id,
            funcionario_id=caixa.funcionario_id,
        )

        date.append(
            {
                "tipo": "FECHAMENTO",
                "valor": valor_fechamento,
                "nome": caixa.nome,
                "descricao": f"Fechamento do caixa - Sistema: {valor_sistema}, "
                             f"Fechamento: {valor_fechamento}, Dif: {caixa.diferenca}",
                "caixa_id": caixa.id,
                "usuario_id": caixa.usuario_id,
                "funcionario_id": caixa.funcionario_id,
            }
        )

        return date

    
    
    @staticmethod
    async def get_caixa_details(user_id: int) -> Dict[str, Any]:
        """
        Retorna o resumo do caixa para fechamento automático:
        - Lista de vendas associadas a este caixa
        - Total por tipo de pagamento
        - Valor total das vendas (valor_sistema)
        """
        # Busca todos os caixas do usuário
        all_cash = await Caixa.filter(usuario_id=user_id).all()

        infos = []
        for caixa in all_cash:
            if not caixa.aberto:  # só processa caixas fechados

                # Busca as vendas ligadas a este caixa
                sales = await Sales.filter(caixa_id=caixa.id).all()

                # Calcula total por forma de pagamento
                total_por_pagamento = {}
                total_sistema = 0
                for sale in sales:
              
                    total_sistema += sale.total_price
                    metodo = sale.payment_method.value
                    total_por_pagamento[metodo] = total_por_pagamento.get(metodo, 0) + sale.total_price

                if caixa.valor_fechamento is not None:
                    # Diferença: Deve esta fora do for
                    diferenca = (caixa.valor_fechamento or 0) - ((caixa.saldo_inicial or 0) + total_sistema)

                else:
                    diferenca = None


                infos.append({
                    "caixa_id": caixa.id,
                    "nome": caixa.nome,
                    "saldo_inicial": caixa.saldo_inicial,
                    "valor_fechamento": caixa.valor_fechamento,
                    "valor_sistema": total_sistema,
                    "diferenca": diferenca,
                    "aberto_em": caixa.criado_em.strftime('%d/%m/%y | %H:%M'),
                    "fechamento": caixa.atualizado_em.strftime('%d/%m/%y | %H:%M'),
                    "total_por_pagamento": total_por_pagamento,
                    "total_vendas": len(sales),
                })

        return infos

    @staticmethod
    async def get_caixa_aberto_funcionario(funcionario_id: int):
        """
        Retorna o caixa aberto de um funcionário, se existir
        """
        return await Caixa.filter(funcionario_id=funcionario_id, aberto=True).first()

    @staticmethod
    async def get_movimentacoes_caixa(caixa_id: int):
        """
        Retorna todas as movimentações de um caixa
        """
        return await CashMovement.filter(caixa_id=caixa_id).order_by('-criado_em')


class FinalizationObjcts:
    def __init__(self, checkout_instance: Checkout = None) -> None:
        self.checkout = checkout_instance
        self.dados_recibo = checkout_instance.receipt_data if checkout_instance else None


        
    async def Updating_cash_values(self, caixa_id: int):
        """
        Passando os campos necessários para atualizar o caixa.
        Este é o último processo em uma venda
        """
        try:
            if not self.checkout:
                raise Exception("Instância do Checkout não fornecida")
            
            # Verifica se há dados do recibo
            if not self.checkout.receipt_data:
                raise Exception("Nenhum dado de venda disponível")
            
            # Obtém informações da venda
            venda_obj = self.checkout.venda
            if not venda_obj or not isinstance(venda_obj, Sales):
                raise Exception("Venda não encontrada ou objeto inválido")
            
            # Calcula valor total da venda
            if isinstance(self.checkout.receipt_data, list):
                valor_total = sum(item.get('total_price', 0) for item in self.checkout.receipt_data)
            else:
                valor_total = self.checkout.receipt_data.get('total_price', 0)
            
            # Obtém forma de pagamento
            forma_pagamento = getattr(self.checkout, 'payment_method', 'PIX')
            
            # Verifica se o caixa existe e está aberto
            caixa = await Caixa.get_or_none(id=caixa_id).prefetch_related('usuario', 'funcionario')
            if not caixa or not caixa.aberto:
                raise Exception("Caixa não encontrado ou fechado")

            # Atualiza saldo do caixa
            caixa.saldo_atual += valor_total
            await caixa.save()

            # Registra movimentação no caixa - CORRIGIDO: passar instâncias completas
            await CashMovement.create(
                tipo="ENTRADA",
                valor=valor_total,
                descricao=f"Venda #{venda_obj.id} - {forma_pagamento}",
                caixa=caixa,  # Instância completa
                usuario=caixa.usuario,  # Instância completa
                funcionario=caixa.funcionario,  # Instância completa (pode ser None)
                venda=venda_obj,  # Instância completa de Sales
            )

            # Atualiza a venda com a referência ao caixa
            venda_obj.caixa = caixa  # Se houver relação inversa
            await venda_obj.save()

            return caixa
            
        except Exception as e:
            print(f"Erro detalhado ao atualizar caixa: {str(e)}")
            raise Exception(f"Erro ao atualizar caixa: {str(e)}")