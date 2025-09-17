from fastapi import HTTPException
import json
from dataclasses import dataclass, field
from src.model.user import Usuario
from datetime import datetime
from zoneinfo import ZoneInfo
from tortoise.functions import Count


class LoginInSystem:

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def _adminSystem(self):
        __data_login = {'username': 'nathec@gmail.com', 'password': '_py3go5BZ}61FhC99kwi'}

        if self.username == __data_login.get('username') and self.password == __data_login.get('password'):
            return True
        else:
            return False




@dataclass
class SystemUser:
    # Iniciando variáveis vazias
    data: list = field(default_factory=list)  # Lista de objetos com informações
    users_active: int = 0  # Quantidade de usuários ativos
    pending: int = 0  # Quantidade de usuários pendentes

    # Verificando se o usuário tem permissão para acessar o sistema
    async def VerifyLogin(self, username, password):
        login = LoginInSystem(username, password)
        result = login._adminSystem()

        if result:
            await self.FeedingSystem()
        else:
            return False

    async def FeedingSystem(self):
        users = await Usuario.all().values("company_name", "cnpj", "cpf", "email", "is_active")

        for customer in users:
            if customer["is_active"]:
                self.users_active += 1
                self.data.append(
                    {
                        "company_name": customer["company_name"],
                        "cnpj": customer["cnpj"],
                        "email": customer["email"],
                        "status": customer["is_active"],
                        "amount": self.users_active,
                    }
                )

    async def UpdateIs_active(self, customer_id: int):
        """Atualiza dados de um cliente"""
        try:
            # Buscando o cliente pelo ID
            customer = await Usuario.filter(id=customer_id).first()
            if customer:
                if customer.is_active:
                    # Desativando a conta
                    await Usuario.filter(id=customer_id).update(is_active=False)
                    return {"aviso": f"Cliente {customer_id} desativado com sucesso!"}
                else:
                    return False
            else:
                raise HTTPException(status_code=404, detail=f"Cliente {customer_id} não encontrado.")

        except Exception as e:
            print("Erro ao atualizar cliente:", e)
            raise HTTPException(status_code=500, detail="Entre em contato com o desenvolvedor.")




    async def UpdateIs_pending(self, customer_id: int):
        """Atualiza dados de um cliente"""
        try:
            # Buscando o cliente pelo ID
            customer = await Usuario.filter(id=customer_id).first()
            if customer:
                if customer.pending:
                    # Desativando a conta
                    await Usuario.filter(id=customer_id).update(pending=False)
                    return {"aviso": f"Cliente {customer.username} agora esta ativo."}
                else:
                    return False
            else:
                raise HTTPException(status_code=404, detail=f"Cliente {customer.username} não encontrado.")

        except Exception as e:
            print("Erro ao atualizar cliente:", e)
            raise HTTPException(status_code=500, detail="Entre em contato com o desenvolvedor.")







    async def ViewInfoCustomes(self, customer_id: int):
        """Visualiza todos os dados do cliente"""
        try:
            customer = await Usuario.filter(id=customer_id).first()

            if customer:
                self.data.append(
                    {
                        "user_data": {
                            "username": customer.username,
                            "email": customer.email,
                            "company_name": customer.company_name,
                            "trade_name": customer.trade_name,
                            "cpf": customer.cpf,
                            "cnpj": customer.cnpj,
                            "state_registration": customer.state_registration,
                            "municipal_registration": customer.municipal_registration,
                            "cnae_principal": customer.cnae_principal,
                            "crt": customer.crt,
                            "cep": customer.cep,
                            "street": customer.street,
                            "home_number": customer.home_number,
                            "complement": customer.complement,
                            "district": customer.district,
                            "city": customer.city,
                            "state": customer.state,
                            "is_active": customer.is_active,
                            "criado_em": customer.criado_em,
                            "pending": customer.pending,

                        }
                    }
                )

                print(self.data)
            else:
                raise HTTPException(status_code=404, detail="Cliente não encontrado")

        except Exception as e:
            print("Erro ao visualizar cliente:", e)
            raise HTTPException(status_code=500, detail=str(e))

    async def UsersPending(self):
        """Retorna a quantidade de usuários pendentes"""
        try:
            # Exemplo: se você tiver um campo `pending=True/False`
            users_pending = await Usuario.filter(pending=True).all()

            if users_pending:
                self.data.append({"pending": len(users_pending)})

            print("-" * 50)
            for i, item in enumerate(self.data, start=1):
                print(f"[{i}] ------------------------------")
                print(json.dumps(item, indent=4, ensure_ascii=False, default=str))  # deixa bonitinho tipo JSON
                print("-" * 50)

        except Exception as e:
            print("Erro em UsersPending:", e)




    async def NewUsersThisMonth(self):
        """Retorna a quantidade de usuários cadastrados no mês atual"""
        try:
            now = datetime.now(ZoneInfo("America/Sao_Paulo"))
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Busca todos os clientes criados a partir do 1º dia do mês
            total = await Usuario.filter(criado_em__gte=start_of_month).count()
            self.data.append({'total_customer': total})

            

        except Exception as e:
            print("Erro ao contar novos clientes:", e)
            return {"novos_clientes_mes": 0}




    def view(self):
        return self.data

   