from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from src.auth.deps import get_current_user
from src.model.user import Ticket
from src.schemas.fornecedor.schema_ticket import TicketCreateSchema, TicketReadSchema
from src.conf.database import engine
from src.model.user import Usuario

router = APIRouter(tags=["Tickets"])


# ========================
# 🔹 Dependência de sessão
# ========================
def get_session():
    with Session(engine) as session:
        yield session


@router.post("/criar", response_model=TicketReadSchema)
async def create_ticket(
    ticket: TicketCreateSchema,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    # Verifica se o usuário já tem um ticket com o mesmo nome
    statement = select(Ticket).where(
        Ticket.name == ticket.name,
        Ticket.usuario_id == current_user.id
    )
    existing_ticket = session.exec(statement).first()

    if existing_ticket:
        raise HTTPException(
            status_code=400,
            detail=f"Você já possui um ticket com o nome '{ticket.name}'"
        )

    # Cria o ticket se não existir duplicado
    db_ticket = Ticket(**ticket.dict(), usuario_id=current_user.id) # type: ignore
    session.add(db_ticket)
    session.commit()
    session.refresh(db_ticket)
    return db_ticket

# ========================
# 🔹 Listar tickets do usuário
# ========================
@router.get("/lista/", response_model=List[TicketReadSchema])
async def list_tickets(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    tickets = session.exec(
        select(Ticket).where(Ticket.usuario_id == current_user.id)
    ).all()
    return tickets


# ========================
# 🔹 Deletar ticket pelo ID
# ========================
@router.delete("/delete/{ticket_id}", response_model=dict)
async def delete_ticket(
    ticket_id: int,
    current_user: Usuario = Depends(get_current_user),
    
    session: Session = Depends(get_session)
):
    ticket = session.get(Ticket, ticket_id)
    if not ticket or ticket.usuario_id != current_user.id:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")

    session.delete(ticket)
    session.commit()
    return {"msg": "Ticket removido com sucesso"}
