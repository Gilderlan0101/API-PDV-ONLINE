from datetime import datetime
from typing import Optional, List
from fastapi import Body, Depends, HTTPException, status, APIRouter, Query
from sqlmodel import Session, select
from ..conf.database import engine
from ..auth.deps import get_current_user
from ..schemas.schema_product import ProductRegisterSchema, ProductUpdateSchema
from ..model.user.users import Produto, Usuario


class Product:
    def __init__(self) -> None:
        # Rota unificada para produtos
        self.router = APIRouter(prefix='/produtos', tags=['Produtos'])
        self.startup_route()

    def startup_route(self):
        # ========================
        # 1️ Criar Produto
        # ========================
        @self.router.post('/', status_code=status.HTTP_201_CREATED)
        async def create_product(
            prod: ProductRegisterSchema,
            current_user: Usuario = Depends(get_current_user),
        ):
            """Cadastra produto vinculado ao usuário logado"""
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                try:
                    # Conversões
                    date_expired = (
                        datetime.combine(
                            prod.date_expired, datetime.min.time()
                        )
                        if prod.date_expired
                        else None
                    )
                    image_url = str(prod.image_url) if prod.image_url else None

                    register_prod = Produto(
                        product_code=prod.product_code,
                        name=prod.name,
                        stock=prod.stock,
                        date_expired=date_expired,
                        fabricator=prod.fabricator,
                        cost_price=prod.cost_price,
                        price_uni=prod.price_uni,
                        sale_price=prod.sale_price,
                        supplier=prod.supplier,
                        lot_bar_code=prod.lot_bar_code,
                        image_url=image_url,
                        usuario_id=current_user.id,
                    )

                    session.add(register_prod)
                    session.commit()
                    session.refresh(register_prod)

                    return {
                        'message': 'Produto cadastrado com sucesso!',
                        'product_id': register_prod.id,
                        'usuario_id': current_user.id,
                    }
                except Exception as e:
                    session.rollback()
                    raise HTTPException(status_code=400, detail=f'Erro: {e}')

        # ========================
        # 2️ Atualizar Produto
        # ========================
        @self.router.put('/', status_code=status.HTTP_200_OK)
        async def update_product(
            code: Optional[str] = Query(None, description='Código do produto'),
            name: Optional[str] = Query(None, description='Nome do produto'),
            update_data: ProductUpdateSchema = Body(...),
            current_user: Usuario = Depends(get_current_user),
        ):
            """Atualiza dados de produto do usuário logado"""
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                query = select(Produto).where(
                    Produto.usuario_id == current_user.id
                )

                if code:
                    query = query.where(Produto.product_code == code)
                elif name:
                    query = query.where(Produto.name == name)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail='Informe código ou nome do produto',
                    )

                product = session.exec(query).first()
                if not product:
                    raise HTTPException(
                        status_code=404, detail='Produto não encontrado'
                    )

                # Atualiza apenas campos informados
                for field, value in update_data.dict(
                    exclude_unset=True
                ).items():
                    if field == 'date_expired' and value:
                        value = datetime.combine(value, datetime.min.time())
                    if field == 'image_url' and value:
                        value = str(value)
                    setattr(product, field, value)

                product.atualizado_em = datetime.now()
                session.add(product)
                session.commit()
                session.refresh(product)

                return {
                    'message': 'Produto atualizado com sucesso!',
                    'product_id': product.id,
                    'dados_atualizados': update_data.dict(exclude_unset=True),
                }

        # ========================
        # 3️ Deletar Produto
        # ========================
        @self.router.delete('/', status_code=status.HTTP_200_OK)
        async def delete_product(
            code: str = Query(..., description='Código do produto'),
            current_user: Usuario = Depends(get_current_user),
        ):
            """Deleta produto do usuário logado"""
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = session.exec(
                    select(Produto)
                    .where(Produto.product_code == code)
                    .where(Produto.usuario_id == current_user.id)
                ).first()

                if not product:
                    raise HTTPException(
                        status_code=404,
                        detail='Produto não encontrado ou não pertence ao usuário',
                    )

                session.delete(product)
                session.commit()

                return {
                    'message': f"Produto '{product.name}' removido com sucesso!",
                    'product_id': product.id,
                    'usuario_id': current_user.id,
                }

        # ========================
        # 4️ Listar Produtos
        # ========================
        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def list_products(
            current_user: Usuario = Depends(get_current_user),
        ) -> List[Produto]:
            """Lista todos os produtos do usuário logado"""
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                products = session.exec(
                    select(Produto).where(
                        Produto.usuario_id == current_user.id
                    )
                ).all()

            return products   # type: ignore
