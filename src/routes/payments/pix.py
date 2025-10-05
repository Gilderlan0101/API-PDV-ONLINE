from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from typing import List
import os

from src.controllers.payments.pix import PixService, PixCreateRequest, PixQRCodeResponse
from src.auth.deps import get_current_user, SystemUser



router = APIRouter()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_pix_account(
    pix_data: PixCreateRequest,
    current_user: SystemUser = Depends(get_current_user),
    pix_service: PixService = Depends(get_current_user)
):
    """
    Cria nova conta PIX para usuário autenticado
    """
    service = PixService(user_id=current_user.id)
    pix_account = await service.create_pix_account(pix_data)
    
    return {
        "message": "Conta PIX criada com sucesso",
        "pix_id": pix_account.id,
        "key_pix": pix_account.key_pix
    }


@router.post("/generate-qrcode", response_model=PixQRCodeResponse)
async def generate_pix_qrcode(
    pix_data: PixCreateRequest,
    current_user: SystemUser = Depends(get_current_user)
):
    """
    Gera QR Code PIX dinâmico
    """
    service = PixService(user_id=current_user.id)
    return await service.generate_qr_code(pix_data)


@router.get("/qrcode-file/{filename}")
async def get_qrcode_file(filename: str):
    """
    Serve arquivo de QR Code gerado
    """
    filepath = f"static/qrcodes/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado"
        )
    
    return FileResponse(
        filepath, 
        media_type='image/png',
        filename=filename
    )


@router.get("/accounts")
async def get_pix_accounts(
    current_user: SystemUser = Depends(get_current_user)
):
    """
    Retorna todas as contas PIX do usuário
    """
    service = PixService(user_id=current_user.id)
    accounts = await service.get_user_pix_accounts()
    
    return {
        "count": len(accounts),
        "accounts": accounts
    }