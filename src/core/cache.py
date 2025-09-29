import redis
import os

# URL completa com usuário, senha, host e porta
REDIS_URL = "redis://default:Tv7qHTyVjk5fxc0QcK55CAKsikJqoJz4@redis-12349.crce196.sa-east-1-2.ec2.redns.redis-cloud.com:12349"

# Cria o cliente
client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

__all__ = ["client"]
