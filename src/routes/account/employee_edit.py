from fastapi import Depends, Query
from .account import employees_router
from src.auth.deps import get_current_user
from src.model.user import Usuario

@employees_router.delete('delete_employee')
async def edit_employee(
    id_employee: int = Query(...),
    current_user: Usuario = Depends(get_current_user)
):
        
    pass