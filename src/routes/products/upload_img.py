from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlmodel import Session, select
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
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")
    
    # Caminho de destino
    file_path = IMAGES_DIR / f"{product_id}_{file.filename}"
    
    # Salva o arquivo
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Atualiza a URL da imagem no banco
    with Session(engine) as session:
        produto = session.get(Produto, product_id)
        if not produto:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        produto.image_url = str(file_path)
        session.add(produto)
        session.commit()
        session.refresh(produto)
    
    return {"message": "Imagem enviada com sucesso", "image_url": produto.image_url}


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
    
    return FileResponse(file_path)
