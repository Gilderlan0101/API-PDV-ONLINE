class Pessoa:

    def __init__(self, name):

        self.name = name


    def __str__(self):

        return self.name


    async def soma(self, number_1, number_2):

        return number_1 + number_2


var = Pessoa('Gilderlan')
print(str(var))
print(var.soma())

