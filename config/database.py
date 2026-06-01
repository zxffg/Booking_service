from psycopg_pool import AsyncConnectionPool
import redis.asyncio as redis

from dotenv import load_dotenv
import os

# ~ БД клиент
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
# conninfo = f"host={DB_HOST} port={DB_PORT} user={DB_USER} password={DB_PASSWORD} dbname={DB_NAME}"
conninfo = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

pool = None
async def init_pool():
    global pool
    pool = AsyncConnectionPool(conninfo=conninfo, min_size=1, max_size=10, open=False)
    await pool.open()

async def get_pool():
    global pool
    if pool is not None:
        return pool
    else:
        await init_pool()
        return pool

# * Redis клиент
client = None
RD_HOST = os.getenv('RD_HOST')
RD_PORT = os.getenv('RD_PORT')
RD_DB = os.getenv('RD_DB')

async def get_redis():
    global client
    if client is None:
        client = redis.Redis(
            host=RD_HOST,
            port=RD_PORT,
            db=RD_DB
        )
    return client