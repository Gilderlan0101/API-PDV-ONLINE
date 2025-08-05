from datetime import datetime, date
from typing import List, Optional
from fastapi import Body, Depends, HTTPException, status, APIRouter, Query
from sqlmodel import SQLModel, Session, select
from ..conf.database import engine
from ..auth.deps import get_current_user
from ..schemas.schema_product import ProductRegisterSchema, ProductUpdateSchema
from ..model.user.users import Produto, Usuario, ProdutoArquivado


class Product:
    def __init__(self) -> None:
        self.router = APIRouter(prefix='/produtos', tags=['Produtos'])
        self.startup_route()

    # ========================
    # 🔹 Helpers internos
    # ========================
    @staticmethod
    def to_dict(model: SQLModel) -> dict:
        """Converte um modelo SQLModel para dict limpo."""
        return {
            k: v for k, v in model.__dict__.items() if not k.startswith('_')
        }

    @staticmethod
    def get_product_by_user(
        session: Session,
        user_id: int,
        code: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Produto]:
        """Busca produto por código ou nome, garantindo que seja do usuário."""
        query = select(Produto).where(Produto.usuario_id == user_id)
        if code:
            query = query.where(Produto.product_code == code)
        if name:
            query = query.where(Produto.name == name)
        return session.exec(query).first()

    def startup_route(self):
        # ========================
        # 1️ Criar Produto
        # ========================
        @self.router.post('/', status_code=status.HTTP_201_CREATED)
        async def create_product(
            prod: ProductRegisterSchema,
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                try:
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
            code: str | None = Query(None, description='Código do produto'),
            name: str | None = Query(None, description='Nome do produto'),
            update_data: ProductUpdateSchema = Body(...),
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = self.get_product_by_user(
                    session, current_user.id, code, name
                )
                if not product:
                    raise HTTPException(
                        status_code=404, detail='Produto não encontrado'
                    )

                # Obtém campos enviados
                data_to_update = update_data.model_dump(exclude_unset=True)
                updated_fields = {}

                for field, value in data_to_update.items():
                    if value in [None, '', 'string']:
                        continue
                    if isinstance(value, (int, float)) and value == 0:
                        continue

                    if field == 'date_expired' and isinstance(value, date):
                        value = datetime.combine(value, datetime.min.time())

                    elif field == 'image_url' and value:
                        value = str(value)

                    if getattr(product, field) != value:
                        setattr(product, field, value)
                        updated_fields[field] = value

                if not updated_fields:
                    return {
                        'message': 'Nenhum campo relevante para atualizar.',
                        'product_id': product.id,
                    }

                product.atualizado_em = datetime.now()
                session.add(product)
                session.commit()
                session.refresh(product)

            return {
                'message': 'Produto atualizado com sucesso!',
                'product_id': product.id,
                'dados_atualizados': updated_fields,
            }

        # ========================
        # 3️ Deletar Produto (com arquivamento)
        # ========================
        @self.router.delete('/', status_code=status.HTTP_200_OK)
        async def delete_product(
            code: str = Query(..., description='Código do produto'),
            description: str = Query(
                ..., description='Motivo do arquivamento'
            ),
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = self.get_product_by_user(
                    session, current_user.id, code
                )
                if not product:
                    raise HTTPException(
                        status_code=404,
                        detail='Produto não encontrado ou não pertence ao usuário',
                    )

                product_data = self.to_dict(product)
                product_data['description'] = description
                product_data.pop('id', None)
                product_data.pop('criado_em', None)
                product_data.pop('atualizado_em', None)

                archived_product = ProdutoArquivado(**product_data)
                session.add(archived_product)
                session.delete(product)
                session.commit()

                return {
                    'message': f"Produto '{product.name}' removido e arquivado com sucesso!",
                    'usuario_id': current_user.id,
                }

        # ========================
        # 4️ Listar Produtos
        # ========================
        @self.router.get('/', status_code=status.HTTP_200_OK)
        async def list_products(
            current_user: Usuario = Depends(get_current_user),
        ) -> List[Produto]:
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                products = session.exec(
                    select(Produto).where(
                        Produto.usuario_id == current_user.id
                    )
                ).all()

            return products[::-1]  # type: ignore # Lista do mais recente para o mais antigo

        # ========================
        # 5️ Registrar Venda
        # ========================
        @self.router.post('/venda', status_code=status.HTTP_200_OK)
        async def register_sale(
            code: str = Query(..., description='Código do produto'),
            quantity: int = Query(..., gt=0, description='Quantidade vendida'),
            current_user: Usuario = Depends(get_current_user),
        ):
            """Registra uma venda simples e reduz o estoque do produto"""
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = self.get_product_by_user(
                    session, current_user.id, code
                )
                if not product:
                    raise HTTPException(
                        status_code=404, detail='Produto não encontrado'
                    )

                if product.stock < quantity:
                    raise HTTPException(
                        status_code=400, detail='Estoque insuficiente'
                    )

                product.stock -= quantity
                product.atualizado_em = datetime.now()
                session.add(product)
                session.commit()
                session.refresh(product)

            return {
                'message': f'Venda registrada: {quantity}x {product.name}',
                'estoque_atual': product.stock,
            }
