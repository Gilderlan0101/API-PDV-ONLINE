from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.auth.deps import get_current_user, SystemUser
from src.controllers.products.inventario.stoke_entry import EntryProducts
from typing import Annotated, Optional

# Renomeando o router para seguir a convenção de PEP 8 (snake_case)
inventory_router = APIRouter(tags=['inventory'])


@inventory_router.post('/generate-entry', status_code=status.HTTP_200_OK)
async def generate_product_entry(
    #  Tornando product_name opcional (default=None)
    product_name: Optional[str] = Query(None, description="Nome do produto que deseja atualizar o estoque."),
    # Adicionando product_code como opcional
    product_code: Optional[str] = Query(None, description="Código do produto que deseja atualizar o estoque."),
    new_stock: int = Query(..., description='Quantos produtos deseja adicionar?'),
    #  Usando Annotated para o campo opcional (já estava correto)
    detail: Annotated[Optional[str], Query(description='Escrever uma pequena descrição')] = None,
    current_user: SystemUser = Depends(get_current_user),
):
    """
    Processa a entrada de novos produtos no estoque para a empresa do usuário logado,
    buscando o item por nome OU código.
    """
    try:
        # Define o ID da empresa. Se for funcionário, usa empresa_id; se for dono, usa o próprio ID.
        # company_id é a única forma de obter o usuário dono da venda, ou seja, o id da empresa.
        company_id = current_user.empresa_id if current_user.empresa_id else current_user.id
        
        # 1. Validação de campos na rota (A validação de "pelo menos um deve ser fornecido"
        #    será feita dentro de EntryProducts.check_fields(), mas podemos adicionar um
        #    check básico aqui para uma resposta HTTP mais limpa).
        if not product_name and not product_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="É obrigatório fornecer o nome OU o código do produto para a busca."
            )
        
        # 2. Instancia a classe EntryProducts
        update_in = EntryProducts(
            company_id=company_id, 
            product_name=product_name, 
            product_code=product_code, # Inclui o código
            new_stock=new_stock, 
            detail=detail
        )

        # 3. Executa a lógica de busca e atualização de estoque
        return await update_in.update_stock()

    except HTTPException as e:
        # Repassa erros HTTP (ex: 400, 404, 401)
        raise e
    except Exception as e:
        # Trata erros inesperados como 500
        print(f"Erro inesperado no controlador de entrada de estoque: {e}")
        # 💡 Usando HTTPException diretamente para um erro 500 limpo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar a entrada de estoque: {str(e)}"
        )






