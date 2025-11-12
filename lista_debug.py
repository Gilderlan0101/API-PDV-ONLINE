def cria_potencia(function):

    def potencia(num):
        return function**num

    return potencia


potencia_2 = cria_potencia(2)
potencia_3 = cria_potencia(3)

print(potencia_2(2))
print(potencia_3(2))


import time


# Define nosso decorator
def calcula_duracao(function):

    def wrapper():
        # Calcular o tempo de execução
        tempo_inicial = time.time()
        function()
        tempo_final = time.time()

        # Formata a mensgem que será mostrada
        print("[{function}] Tempo total de execução: {tempo_total}".format(function=function.__name__, tempo_total=str(tempo_final - tempo_inicial)))

    return wrapper


# Decora a função com o decorator
@calcula_duracao
def main():

    for n in range(0, 100000000):
        pass


# Executa a função main
main()
