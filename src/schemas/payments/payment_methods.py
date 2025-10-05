from src.auth.deps import SystemUser
from pydantic import BaseModel
from typing import Optional

# ID_USER =  SystemUser.id


class RegisterUserForPartialMode(BaseModel):
    full_name: str
    cpf: str
    tel: int
    user_id: int


class InputData(BaseModel):
    product_name: str
    total_price: int
    cpf: str


class PartialDataOutput(BaseModel):
    """Saída de dados ao finalizar uma venda"""

    full_name: str
    value: int
    mensagem: Optional[dict]  # ex: {'mensagem': 'O cliente X pagou 30.00 de 100.00 restante 70.00'}


class ReceivePaymentPartial(BaseModel):
    """Receber pagamento do usuario"""

    cpf: str
    value_received: float
    type_meyhod_payment: str
