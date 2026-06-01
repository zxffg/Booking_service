import asyncio
from config.database import init_pool, get_pool, get_redis, conninfo

print("conninfo:", conninfo)

async def test():
    await init_pool()
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            result = await cur.fetchone()
            print(f"Postgres is {result[0]}")
    
    client = await get_redis()
    pong = await client.ping()
    print(f"Redis is {pong}")

asyncio.run(test())