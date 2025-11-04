class Car:
    def __init__(self, car_name):

        self.name = car_name

    def createcar(self):

        return f'Carro {self.name} foi criado'


car = Car('Honda')
print(car.createcar())
