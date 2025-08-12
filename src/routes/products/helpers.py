from typing import Optional
from sqlmodel import Session, select
from src.model.product import Produto
from sqlmodel import SQLModel

def to_dict(model: SQLModel) -> dict:
    return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}

def get_product_by_user(
    session: Session,
    user_id: int,
    code: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Produto]:
    query = select(Produto).where(Produto.usuario_id == user_id)
    if code:
        query = query.where(Produto.product_code == code)
    if name:
        query = query.where(Produto.name == name)
    return session.exec(query).first()
