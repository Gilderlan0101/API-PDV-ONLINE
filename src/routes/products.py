import json
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, SQLModel, select

from src.auth.deps import get_current_user
from src.conf.database import engine
from src.controllers.sales.sales import Checkout
from src.model.user.users import Produto, ProdutoArquivado, Usuario
from src.schemas.schema_product import ProductRegisterSchema, ProductUpdateSchema
from src.schemas.avisos import RelatorioOut, ResponseOut
from src.controllers.stoke.stoke_control import gerar_relatorio_completo


from pydantic import ValidationError, model_validator



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
        return {k: v for k, v in model.__dict__.items() if not k.startswith('_')}

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
        @self.router.post('/create', status_code=status.HTTP_201_CREATED)
        async def create_product(
            prod: ProductRegisterSchema,
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                try:
                    date_expired = (
                        datetime.combine(prod.date_expired, datetime.min.time())
                        if prod.date_expired
                        else None
                    )
                    image_url = str(prod.image_url) if prod.image_url else None

                    register_prod = Produto(
                        product_code=prod.product_code,
                        name=prod.name,
                        stock=prod.stock,
                        stoke_min=prod.stoke_min,
                        stoke_max=prod.stoke_max,
                        date_expired=date_expired,
                        fabricator=prod.fabricator,
                        cost_price=prod.cost_price,
                        price_uni=prod.price_uni,
                        sale_price=prod.sale_price,
                        supplier=prod.supplier,
                        lot_bar_code=prod.lot_bar_code,
                        image_url=image_url, # Devemos verifica se a img do produto esta correta
                        usuario_id=current_user.id,
                        # 🔹 Campos extras do schema
                        product_type=prod.product_type,
                        active=prod.active,
                        group=prod.group,
                        sector=prod.sector,
                        unit=prod.unit,
                        controllstoke=prod.controllstoke,
                        sales_config=(
                            prod.sales_config.json() if prod.sales_config else None
                        ),
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
        @self.router.put('/update', status_code=status.HTTP_200_OK)
        async def update_product(
            code: str | None = Query(None, description='Código do produto'),
            name: str | None = Query(None, description='Nome do produto'),
            update_data: ProductUpdateSchema = Body(...),
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = self.get_product_by_user(session, current_user.id, code, name)
                if not product:
                    raise HTTPException(
                        status_code=404, detail='Produto não encontrado'
                    )

                # Obtém campos enviados
                data_to_update = update_data.model_dump(exclude_unset=True)
                updated_fields = {}

                for field, value in data_to_update.items():
                    if isinstance(value, dict):
                        value = json.dumps(
                            value, ensure_ascii=False
                        )  # Converte dict -> str JSON

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
        @self.router.delete('/delete', status_code=status.HTTP_200_OK)
        async def delete_product(
            code: str = Query(..., description='Código do produto'),
            description: str = Query(..., description='Motivo do arquivamento'),
            current_user: Usuario = Depends(get_current_user),
        ):
            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            with Session(engine) as session:
                product = self.get_product_by_user(session, current_user.id, code)
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
        @self.router.get('/list', response_model=ResponseOut)
        async def list_products(current_user: Usuario = Depends(get_current_user)):
            try:
                if not current_user.id:
                    raise HTTPException(status_code=400, detail='Usuário inválido')

                with Session(engine) as session:
                    produtos_orm = session.exec(
                        select(Produto).where(Produto.usuario_id == current_user.id)
                    ).all()

               # Montar a lista no formato esperado pelo schema
                products = []
                for p in produtos_orm:
                    products.append({
                        "product_code": p.product_code,
                        "id": p.id,
                        "name": p.name,
                        "sale_price": p.sale_price,
                        "stock_atual": p.stock,
                        "stock_min": p.stoke_min,
                        "stock_max": p.stoke_max,
                        "date_expired": p.date_expired.isoformat() if p.date_expired else None,
                        "price_uni": p.price_uni,
                    })
                    
                    
                
                relatorios_dict = gerar_relatorio_completo(current_user.id)
                

                try:
                    relatorios_obj = RelatorioOut.model_validate(relatorios_dict)
                except ValidationError as e:
                    print('Erro na validação do relatório:', e)
                    raise HTTPException(status_code=500, detail='Erro no formato do relatório')

                return {
                    'products': products,  # agora é uma lista de dict no formato esperado
                    'aviso': relatorios_obj
                }

            except Exception as e:
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e)},
                )




        @self.router.post('/sales', status_code=status.HTTP_200_OK)
        async def register_sale(
            code: str = Query(..., description='Código do produto'),
            quantity: int = Query(..., gt=0, description='Quantidade vendida'),
            payment_method: str = Query(
                ..., description='Forma de pagamento: dinheiro, cartão, pix'
            ),
            current_user: Usuario = Depends(get_current_user),
        ):

            if not current_user.id:
                raise HTTPException(status_code=400, detail='Usuário inválido')

            checkout = Checkout(
                user_id=current_user.id,
                product_name='',
                quantity=quantity,
                total_price=0.0,
                lucro_total=0.0,
                payment_method=payment_method,
            )

            nota_fiscal = checkout.process_sale(
                current_user,
                product_code=code,
                quantity=quantity,
                payment_method=payment_method,
            )

            return nota_fiscal
