import requests

cnpj = '19131243000197'  # exemplo
url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj}'

resposta = requests.get(url)
dados = resposta.json()

print(dados['nome'])          # Razão Social
print(dados['fantasia'])      # Nome Fantasia
print(dados['qsa'])           # Lista de sócios
print(dados['telefone'])
