from dataclasses import dataclass, field


@dataclass
class Note(Checkout):
    """Extensão de Checkout para gerar notas fiscais adicionais"""

    async def verifyFields(self) -> bool:
        """Verifica campos obrigatórios"""
        campos_obrigatorios = [
            self.user_id,
            self.product_name,
            self.quantity,
            self.produto_id,
        ]
        if not all(campos_obrigatorios):
            raise HTTPException(status_code=400, detail="Preencha todos os campos obrigatórios.")
        if self.quantity <= 0:
            raise HTTPException(status_code=400, detail="A quantidade deve ser maior que zero.")
        return True

    async def createNote(self) -> dict:
        """Cria uma nota fiscal"""
        await self.verify_datas()
        await self.verifyFields()

        # Lógica específica para criação de nota
        if self.receipt_data:
            print(self.receipt_data)
            return self.build_receipt(self.receipt_data)
        else:
            raise HTTPException(status_code=400, detail="Nenhum dado de venda disponível")
