# src/controllers/cash_controller.py
from tortoise.transactions import in_transaction
from datetime import datetime
from zoneinfo import ZoneInfo
from src.model.cashmovement import CashMovement
from src.model.caixa import Caixa


class CashController:

    @staticmethod
    async def abrir_caixa(usuario_id: int, funcionario_id: int, saldo_inicial: float, nome: str = "Caixa Principal"):
        """
        Abre um novo caixa para um funcionário
        """
        async with in_transaction() as conn:
            # Verifica se já existe caixa aberto para este funcionário
            caixa_aberto = await Caixa.filter(funcionario_id=funcionario_id, aberto=True).first()

            match caixa_aberto:

                case True:
                    raise Exception("Já existe um caixa aberto para este funcionário")

                case _:
                    # Cria novo caixa
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
    async def registrar_venda_caixa(caixa_id: int, venda_id: int, valor_venda: float, forma_pagamento: str):
        """
        Registra uma venda no caixa e atualiza o saldo
        """

        caixa = await Caixa.get_or_none(id=caixa_id)

        match not caixa or not caixa.aberto:
            case False:
                raise Exception("Caixa não encontrado ou fechado")

            case _:
                # Atualiza saldo do caixa
                caixa.saldo_atual += valor_venda
                await caixa.save()
                # Registra movimentação
                await CashMovement.create(
                    tipo="ENTRADA",
                    valor=valor_venda,
                    descricao=f"Venda #{venda_id} - {forma_pagamento}",
                    caixa_id=caixa.id,
                    usuario_id=caixa.usuario_id,
                    funcionario_id=caixa.funcionario_id,
                    venda_id=venda_id,
                )
        return caixa

    @staticmethod
    async def fechar_caixa(caixa_id: int):
        """
        Fecha o caixa e calcula as diferenças
        """

        caixa = await Caixa.get_or_none(id=caixa_id)

        match not caixa or not caixa.aberto:

            case False:
                raise Exception("Caixa não encontrado ou já fechado")

            case _:
                # Calcula valor do sistema (saldo inicial + entradas - saídas)
                entradas = await CashMovement.filter(caixa_id=caixa_id, tipo__in=["ENTRADA", "ABERTURA"]).all()

                saidas = await CashMovement.filter(caixa_id=caixa_id, tipo="SAIDA").all()

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

                # Registra movimentação de fechamento
                await CashMovement.create(
                    tipo="FECHAMENTO",
                    valor=valor_fechamento,
                    descricao=f"Fechamento do caixa - Sistema: {valor_sistema}, Fechamento: {valor_fechamento}, Dif: {caixa.diferenca}",
                    caixa_id=caixa.id,
                    usuario_id=caixa.usuario_id,
                    funcionario_id=caixa.funcionario_id,
                )

        return caixa

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
