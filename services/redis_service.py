import redis.asyncio
from config.database import get_redis

from datetime import datetime

# Наложение блокировки
async def acquire_lock(room_id: int) -> bool:
    try:
        client = await get_redis()
        result = await client.set(f"lock:room:{room_id}", "locked", nx=True, ex=600)
        return result is not None
    except Exception as e:
        raise e
    
# Снятие блокировки
async def release_lock(room_id: int) -> bool:
    try:
        client = await get_redis()
        result = await client.delete(f"lock:room:{room_id}")
        return result > 0
    except Exception as e:
        raise e

# Запись времени до конца брони
async def set_booking_cache(room_id: int, check_in: str, check_out: str) -> bool:
    try:
        client = await get_redis()
        seconds = (datetime.strftime(check_out, "%Y-%m-%d") - datetime.strftime(check_in, "%Y-%m-%d")).total_seconds()
        result = await client.set(f"booking:room:{room_id}", "booked", nx=True, ex=int(seconds))
        return result is not None
    except Exception as e:
        raise e

# удалить запись о брони и время
async def delete_booking_cache(room_id: int) -> bool:
    try:
        client = await get_redis()
        result = await client.delete(f"booking:room:{room_id}")
        return result > 0
    except Exception as e:
        raise e

# проверить есть ли блокировка или кеш (бронь)
async def is_room_locked(room_id: int) -> bool:
    try:
        client = await get_redis()
        return bool((await client.exists(f"booking:room:{room_id}")) or (client.exists(f"lock:room:{room_id}")))
    except Exception as e:
        raise e