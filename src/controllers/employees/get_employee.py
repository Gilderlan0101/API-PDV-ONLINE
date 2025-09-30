from http.client import HTTPException
import tortoise
import tortoise.exceptions
from src.model.employee import Employees
from src.schemas.funcs.registre_funcs import OutputFormat
from fastapi import HTTPException


async def getEmployees(user_id: int):
    '''GetEmployees Busca todos os fucionarios do usuario admin
    parms: user_id: int | None
    '''
    connection = None
    try:
        # Estabelecer conexão explicitamente se necessário
        connection = tortoise.Tortoise.get_connection("default")

        employees = await Employees.filter(usuario_id=user_id).all()
        employee_information = []

        match employees:

            case employees if len(employees) > 0:
                for date in employees:

                    formate_data = OutputFormat(nome=date.nome, cargo=date.cargo, email=date.email, telefone=date.telefone, ativo=date.ativo)
                    if date.ativo is True:
                        employee_information.append(
                            {   
                                "id": date.id,
                                'nome': formate_data.nome,
                                'cargo': formate_data.cargo,
                                'email': formate_data.email,
                                'telefone': formate_data.telefone or '',
                                'ativo': formate_data.ativo,
                            }
                        )

                return employee_information

            case _:
                return {'status': False, 'message': 'Nemhum fucionario cadastrado'}

    except tortoise.exceptions.DoesNotExist:
        raise HTTPException(status_code=404, detail='Usuario não encontrado. Faça login para prosseguir.')

    except tortoise.exceptions.BaseORMException:
        raise HTTPException(status_code=500, detail='Estamos enfrentando problemas internos, tente mais tarde ou entre em contato com o suporte.')

    finally:

        try:
            if connection:
                await connection.close()
        except tortoise.exceptions.BaseORMException:
            connection = tortoise.Tortoise.get_connection("default")
            await connection.close()
