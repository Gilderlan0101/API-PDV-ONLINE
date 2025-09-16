from fastapi import HTTPException
from src.model.employee import Employees
import tortoise.exceptions


async def updatedateEmployee(user_id: int, id_employee: int):
    '''
    updatedateEmployee: Função para atualizar os dados dos fucionarios
    parms: user_id: int id
    parms: id_employee: int id
    '''

    try:

        #
        employees = await Employees.filter(usuario_id=user_id, id=id_employee).first()

        match employees:

            case employees if employees is not None:
                pass

            case _:
                raise HTTPException(status_code=404, detail='Usuario não encontrado.')

    except tortoise.exceptions.BaseORMException:
        pass

    finally:
        try:
            pass

        except tortoise.exceptions.BaseORMException:
            pass
