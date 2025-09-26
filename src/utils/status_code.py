# status_codes.py

# ✅ 2xx Success
HTTP_200_OK = 200  # Requisição bem-sucedida
HTTP_201_CREATED = 201  # Recurso criado com sucesso
HTTP_202_ACCEPTED = 202  # Requisição aceita para processamento (assíncrono)
HTTP_204_NO_CONTENT = 204  # Sucesso, mas sem conteúdo no corpo da resposta

# 🔄 3xx Redirection
HTTP_301_MOVED_PERMANENTLY = 301  # Recurso movido permanentemente para outra URL
HTTP_302_FOUND = 302  # Redirecionamento temporário
HTTP_304_NOT_MODIFIED = 304  # Conteúdo não foi modificado (cache)

# ⚠️ 4xx Client Errors
HTTP_400_BAD_REQUEST = 400  # Requisição inválida (erro de sintaxe ou parâmetros)
HTTP_401_UNAUTHORIZED = 401  # Não autorizado (necessário autenticação)
HTTP_403_FORBIDDEN = 403  # Acesso proibido (credenciais não têm permissão)
HTTP_404_NOT_FOUND = 404  # Recurso não encontrado
HTTP_405_METHOD_NOT_ALLOWED = 405  # Método HTTP não permitido para esse endpoint
HTTP_409_CONFLICT = 409  # Conflito (ex: recurso já existe)
HTTP_422_UNPROCESSABLE_ENTITY = 422  # Erro de validação (dados enviados são inválidos)

# 💀 5xx Server Errors
HTTP_500_INTERNAL_SERVER_ERROR = 500  # Erro interno do servidor
HTTP_501_NOT_IMPLEMENTED = 501  # Funcionalidade não implementada no servidor
HTTP_502_BAD_GATEWAY = 502  # Resposta inválida de outro servidor/proxy
HTTP_503_SERVICE_UNAVAILABLE = 503  # Serviço indisponível (servidor fora do ar/overload)

__all__ = [
    "HTTP_200_OK",
    "HTTP_201_CREATED",
    "HTTP_202_ACCEPTED",
    "HTTP_204_NO_CONTENT",
    "HTTP_301_MOVED_PERMANENTLY",
    "HTTP_302_FOUND",
    "HTTP_304_NOT_MODIFIED",
    "HTTP_400_BAD_REQUEST",
    "HTTP_401_UNAUTHORIZED",
    "HTTP_403_FORBIDDEN",
    "HTTP_404_NOT_FOUND",
    "HTTP_405_METHOD_NOT_ALLOWED",
    "HTTP_409_CONFLICT",
    "HTTP_422_UNPROCESSABLE_ENTITY",
    "HTTP_500_INTERNAL_SERVER_ERROR",
    "HTTP_501_NOT_IMPLEMENTED",
    "HTTP_502_BAD_GATEWAY",
    "HTTP_503_SERVICE_UNAVAILABLE",
]
