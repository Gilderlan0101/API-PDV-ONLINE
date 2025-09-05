lista = ['dd11', 'dd11', 'dd12', 'dd11']

vendas = 0


for i, valor_atual in enumerate(lista):
    if i < len(lista) - 1:
        proximo_valor = lista[i + 1]
        print(f"Índice {i}: {valor_atual} vs Índice {i+1}: {proximo_valor}")

        if valor_atual != proximo_valor:
            vendas += 1

        if valor_atual == proximo_valor:
            print([valor_atual, proximo_valor])

    else:
        print(f"Fim da lista. Não há próximo valor para o índice {i}.")
print(vendas)
