from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlmodel import Session
from src.conf.database import engine
from src.model.product import Produto

router = APIRouter()

# Diretório onde as imagens serão salvas
IMAGES_DIR = Path("static/images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ===============================
# Upload de imagem do produto
# ===============================
@router.post("/produto/{product_id}/upload-imagem")
async def upload_image(product_id: int, file: UploadFile = File(...)):
    # Verifica extensão permitida
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")

    # Gera nome único para o arquivo
    unique_filename = f"{product_id}{file_ext}"
    file_path = IMAGES_DIR / unique_filename

    # Salva o arquivo
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Atualiza a URL da imagem no banco
    with Session(engine) as session:
        produto = session.get(Produto, product_id)
        if not produto:
            # Remove o arquivo se o produto não existir
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        # Remove imagem anterior se existir
        if produto.image_url:
            old_path = Path(produto.image_url)
            if old_path.exists() and old_path != file_path:
                old_path.unlink()

        produto.image_url = str(file_path)
        session.add(produto)
        session.commit()

    return {
        "message": "Imagem enviada com sucesso",
        "image_url": f"/sales/upload/produto/{product_id}/imagem"
    }


# ===============================
# Exibir imagem do produto
# ===============================
@router.get("/produto/{product_id}/imagem")
async def get_image(product_id: int):
    with Session(engine) as session:
        produto = session.get(Produto, product_id)
        if not produto or not produto.image_url:
            raise HTTPException(status_code=404, detail="Imagem não encontrada")

    file_path = Path(produto.image_url)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de imagem não encontrado")

    # Define Content-Type com base na extensão
    extension_to_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    content_type = extension_to_type.get(file_path.suffix.lower(), "image/jpeg")

    # Retorna a imagem com headers CORS
    return FileResponse(
        file_path,
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Cache-Control": "public, max-age=3600"
        }
    )


# ===============================
# Rota OPTIONS para CORS preflight
# ===============================
@router.options("/produto/{product_id}/imagem")
async def options_image(product_id: int):
    return {
        "Allow": "GET, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }
