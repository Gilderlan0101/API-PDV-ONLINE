⚠️ PDV API — Em Desenvolvimento

Aviso: Esta API ainda está em fase de desenvolvimento e pode apresentar instabilidades ou erros inesperados.
🚀 Como rodar o projeto
1. Pré‑requisitos

    Python 3.12 ou superior

    Poetry (gerenciador de pacotes)

2. Instalar Poetry
Linux/macOS

curl -sSL https://install.python-poetry.org | python3 -
# Reinicie o terminal ou ajuste o PATH conforme instruções do instalador

Windows (PowerShell como Administrador)

(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
# Reinicie o PowerShell

Verifique:

poetry --version

3. Clonar o projeto e instalar dependências

git clone https://github.com/Gilderlan0101/API-PDV-ONLINE.git
cd API-PDV-ONLINE
git checkout dev
poetry install

4. Ativar o ambiente virtual do Poetry

poetry env info --path

    Linux/macOS

source $(poetry env info --path)/bin/activate

Windows (PowerShell)

    & (poetry env info --path)\Scripts\activate

5. Permissão e execução do dev.sh
Linux/macOS

chmod +x dev.sh
./dev.sh

Windows

.\dev.sh

O script dev.sh automaticamente ativa o ambiente, instala dependências (se necessário) e executa o servidor FastAPI.
🎯 Endpoints disponíveis

Servidor padrão:

http://127.0.0.1:8000

    Swagger UI: /docs

    ReDoc: /redoc

🔑 Passo a passo para autenticação no Swagger

    Acesse http://127.0.0.1:8000/docs

    Vá até a rota POST /auth/login

    Faça login com o usuário de teste:

email: admin@test.com
senha: 123456

    Ao executar a rota, será retornado um access_token e um refresh_token.

    Copie o access_token.

    No canto superior direito do Swagger, clique em Authorize.

    Na última opção (bearerAuth):

        Value: Bearer <access_token>

    Nos campos username e password, preencha com o email e senha do usuário.

    Clique em Authorize e feche a janela.

Agora todas as rotas autenticadas estarão liberadas para testes. 🎉
👤 Usuário de teste já criado

user1 = Usuario(
    username='admin',
    email='admin@test.com',
    password=bcrypt.hash('123456'),
    company_name='Empresa Teste 1',
    trade_name='Loja Central',
    membros=1,
    cnpj='12345678000199',
    city='São Paulo',
    state='SP',
)

📦 Rotas principais
🧾 Autenticação

    POST /auth/login → Login via formulário OAuth2, retorna access_token e refresh_token

📦 Produtos (/produtos)

    POST / → Criar produto

    PUT / → Atualizar produto (por código ou nome)

    DELETE / → Arquivar e deletar produto (exige código + motivo)

    GET / → Listar produtos do usuário

    POST /venda → Registrar venda, reduz estoque

🧪 Dados de teste

    Usuário admin@test.com com senha 123456 já criado

    Produtos e afiliados de teste já carregados no banco ao iniciar a aplicação