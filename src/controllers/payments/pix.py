from fastapi import HTTPException, status
import requests
import logging
from typing import Dict, Any, Optional
from src.model.pix import Pix
from pydantic import BaseModel, validator, constr
import re

# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes
MIN_NAME_SIZE = 10
MIN_CITY_SIZE = 5
PIX_API_URL = "https://gerarqrcodepix.com.br/api/v1"
VALID_PIX_TYPES = {'qr', 'br'}


class PixCreateRequest(BaseModel):
    """Schema para criação de PIX"""
    full_name: constr(min_length=MIN_NAME_SIZE, max_length=90)
    city: constr(min_length=MIN_CITY_SIZE, max_length=90)
    key_pix: str
    value: float
    type_exit: str = 'qr'

    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.replace(' ', '').isalpha():
            raise ValueError('Nome deve conter apenas letras e espaços')
        return v.title()

    @validator('key_pix')
    def validate_key_pix(cls, v):
        if not v or v.strip() == "#":
            raise ValueError('Chave PIX é obrigatória')
        
        # Validação básica de formato de chave PIX
        if len(v) < 5:
            raise ValueError('Chave PIX muito curta')
        
        return v.strip()

    @validator('value')
    def validate_value(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser maior que zero')
        if v > 1000000:  # Limite de 1 milhão
            raise ValueError('Valor muito alto')
        return round(v, 2)

    @validator('type_exit')
    def validate_type_exit(cls, v):
        if v not in VALID_PIX_TYPES:
            raise ValueError(f'Tipo de saída deve ser: {", ".join(VALID_PIX_TYPES)}')
        return v


class PixQRCodeResponse(BaseModel):
    """Response para geração de QR Code"""
    success: bool
    qr_code_file: Optional[str] = None
    br_code: Optional[str] = None
    message: str
    transaction_data: Optional[Dict] = None


class PixService:
    """
    Service para gerenciamento de operações PIX
    """

    def __init__(self, user_id: int):
        self.user_id = user_id

    async def _validate_pix_data(self, pix_data: PixCreateRequest) -> bool:
        """
        Valida dados do PIX antes do processamento
        """
        try:
            # Verifica se usuário já tem PIX com mesma chave
            existing_pix = await Pix.filter(
                usuario_id=self.user_id, 
                key_pix=pix_data.key_pix,
                is_active=True
            ).first()
            
            if existing_pix:
                logger.warning(f"Usuário {self.user_id} tentou cadastrar chave PIX duplicada: {pix_data.key_pix}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Chave PIX já cadastrada para este usuário"
                )

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro na validação PIX: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno na validação dos dados"
            )

    async def create_pix_account(self, pix_data: PixCreateRequest) -> Pix:
        """
        Cria uma nova conta PIX para o usuário
        """
        try:
            # Valida dados
            await self._validate_pix_data(pix_data)

            # Cria registro no banco
            pix_account = await Pix.create(
                full_name=pix_data.full_name,
                city=pix_data.city,
                key_pix=pix_data.key_pix,
                usuario_id=self.user_id
            )

            logger.info(f"Conta PIX criada com sucesso para usuário {self.user_id}")
            return pix_account

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao criar conta PIX: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao criar conta PIX"
            )

    async def generate_qr_code(self, pix_data: PixCreateRequest) -> PixQRCodeResponse:
        """
        Gera QR Code PIX dinâmico
        """
        try:
            # Parâmetros para a API
            params = {
                "nome": pix_data.full_name,
                "cidade": pix_data.city,
                "chave": pix_data.key_pix,
                "valor": f"{pix_data.value:.2f}",
                "saida": pix_data.type_exit
            }

            logger.info(f"Gerando QR Code PIX para usuário {self.user_id}")

            # Requisição para API externa
            response = requests.get(
                PIX_API_URL, 
                params=params, 
                timeout=30,
                headers={'User-Agent': 'PIX-Service/1.0'}
            )

            if response.status_code != 200:
                logger.error(f"API PIX retornou erro: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Serviço de QR Code indisponível"
                )

            # Processa resposta baseada no tipo de saída
            if pix_data.type_exit == 'qr':
                import os
                from datetime import datetime

                # Cria diretório se não existir
                os.makedirs("static/qrcodes", exist_ok=True)

                # Gera nome do arquivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"qrcode_{self.user_id}_{timestamp}.png"
                filepath = f"static/qrcodes/{filename}"

                # Salva imagem
                with open(filepath, "wb") as f:
                    f.write(response.content)

                logger.info(f"QR Code gerado: {filename}")

                return PixQRCodeResponse(
                    success=True,
                    qr_code_file=filepath,
                    message="QR Code gerado com sucesso",
                    transaction_data={
                        "value": pix_data.value,
                        "receiver": pix_data.full_name,
                        "timestamp": timestamp
                    }
                )

            else:  # type_exit == 'br'
                br_code = response.text.strip()
                
                return PixQRCodeResponse(
                    success=True,
                    br_code=br_code,
                    message="Código BR PIX gerado com sucesso",
                    transaction_data={
                        "value": pix_data.value,
                        "receiver": pix_data.full_name
                    }
                )

        except requests.exceptions.Timeout:
            logger.error("Timeout na geração do QR Code PIX")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tempo limite excedido na geração do QR Code"
            )
        except requests.exceptions.ConnectionError:
            logger.error("Erro de conexão na API PIX")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço de PIX indisponível"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado na geração QR Code: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno na geração do QR Code"
            )

    async def get_user_pix_accounts(self) -> list[Pix]:
        """
        Retorna todas as contas PIX ativas do usuário
        """
        try:
            return await Pix.filter(
                usuario_id=self.user_id, 
                is_active=True
            ).order_by('-created_at')
        
        except Exception as e:
            logger.error(f"Erro ao buscar contas PIX: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao buscar contas PIX"
            )

    async def deactivate_pix_account(self, pix_id: int) -> bool:
        """
        Desativa uma conta PIX
        """
        try:
            pix_account = await Pix.filter(
                id=pix_id, 
                usuario_id=self.user_id
            ).first()

            if not pix_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conta PIX não encontrada"
                )

            pix_account.is_active = False
            await pix_account.save()

            logger.info(f"Conta PIX {pix_id} desativada para usuário {self.user_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao desativar conta PIX: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao desativar conta PIX"
            )