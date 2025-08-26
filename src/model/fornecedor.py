# from __future__ import annotations
# from typing import TYPE_CHECKING, List, Optional


# from datetime import datetime, date
# from enum import Enum

# from sqlmodel import SQLModel, Field, Column, JSON, Relationship, String, Text

# if TYPE_CHECKING:
#     from src.model.user import Usuario

# # =========================
# # Enums
# # =========================
# class SupplierType(str, Enum):
#     PESSOA_JURIDICA = "PJ"
#     PESSOA_FISICA = "PF"

# class TaxRegime(str, Enum):
#     SIMPLES_NACIONAL = "Simples Nacional"
#     LUCRO_PRESUMIDO = "Lucro Presumido"
#     LUCRO_REAL = "Lucro Real"
#     MEI = "MEI"
#     OUTRO = "Outro"

# class IEStatus(str, Enum):
#     CONTRIBUINTE = "Contribuinte"
#     ISENTO = "Isento"
#     NAO_CONTRIBUINTE = "Não Contribuinte"

# class PaymentTerm(str, Enum):
#     AVISTA = "À vista"
#     DIAS_7 = "7 dias"
#     DIAS_14 = "14 dias"
#     DIAS_21 = "21 dias"
#     DIAS_28 = "28 dias"
#     DIAS_30 = "30 dias"
#     DIAS_45 = "45 dias"
#     DIAS_60 = "60 dias"
#     PERSONALIZADO = "Personalizado"

# class SupplierStatus(str, Enum):
#     ATIVO = "Ativo"
#     INATIVO = "Inativo"
#     BLOQUEADO = "Bloqueado"
#     PENDENTE = "Pendente"
    
    
# # =========================
# # Modelo principal: Fornecedor
# # =========================
# class Fornecedor(SQLModel, table=True):

#     id: Optional[int] = Field(default=None, primary_key=True)

#     # Identificação
#     tipo: SupplierType = Field(default=SupplierType.PESSOA_JURIDICA, index=True)
#     razao_social: str = Field(sa_column=Column("razao_social", String(200), nullable=False))
#     nome_fantasia: Optional[str] = Field(default=None, sa_column=Column(String(200)))

#     # Documentos
#     cnpj: Optional[str] = Field(default=None, sa_column=Column(String(14), unique=True, index=True))
#     cpf: Optional[str] = Field(default=None, sa_column=Column(String(11), unique=True, index=True))
#     ie_status: IEStatus = Field(default=IEStatus.CONTRIBUINTE)
#     inscricao_estadual: Optional[str] = Field(default=None, sa_column=Column(String(20)))
#     inscricao_municipal: Optional[str] = Field(default=None, sa_column=Column(String(20)))

#     # Fiscal
#     regime_tributario: TaxRegime = Field(default=TaxRegime.SIMPLES_NACIONAL)

#     # Contatos
#     email: Optional[str] = Field(default=None, sa_column=Column(String(200)))
#     telefones: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
#     site: Optional[str] = Field(default=None, sa_column=Column(String(200)))
#     contato_principal: Optional[dict] = Field(default=None, sa_column=Column(JSON))
#     contatos_secundarios: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))

#     # Endereço
#     endereco: Optional[dict] = Field(default=None, sa_column=Column(JSON))

#     # Financeiro
#     prazo_pagamento: PaymentTerm = Field(default=PaymentTerm.DIAS_30)
#     prazo_personalizado_dias: Optional[int] = None
#     limite_credito: float = Field(default=0)
#     desconto_padrao_percent: float = Field(default=0)

#     # Bancário
#     contas_bancarias: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))

#     # Operacional
#     categorias_fornecimento: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
#     observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))
#     status: SupplierStatus = Field(default=SupplierStatus.ATIVO)

#     # Auditoria
#     criado_em: datetime = Field(default_factory=datetime.now)
#     atualizado_em: datetime = Field(default_factory=datetime.now)
#     ativo_desde: Optional[date] = None
#     criado_por: Optional[str] = Field(default=None, sa_column=Column(String(100)))
#     atualizado_por: Optional[str] = Field(default=None, sa_column=Column(String(100)))

#     # Chave estrangeira para usuário
#     usuario_id: int = Field(foreign_key="usuarios.id", nullable=False)
#     usuario: Optional["Usuario"] = Relationship(back_populates="fornecedores")


# # =========================
# # 🔹 Resolver forward refs do SQLModel
# # =========================
# Fornecedor.model_rebuild()
