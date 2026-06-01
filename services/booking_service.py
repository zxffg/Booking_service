from db.repository import create_booking, check_overlap
from services.redis_service import (acquire_lock, release_lock, set_booking_cache, 
                                    delete_booking_cache, is_room_locked)

from datetime import datetime

# классы исключений которые могут возникнуть
class RoomLockedException(Exception):
    pass

class AcquireRoomException(Exception):
    pass

class TimeOverlapException(Exception):
    pass

class CreateBookingException(Exception):
    pass

class CacheException(Exception):
    pass

class ReleaseLockException(Exception):
    pass

#! Бизнес логика бронирования
async def create_booking_flow(user_id: int, room_id: int, check_in: str, check_out: str) -> None:
    lock_acquire = False
    try:
        if await is_room_locked(room_id):
            raise RoomLockedException
        
        if not await acquire_lock(room_id):
            raise AcquireRoomException
        lock_acquire = True

        if await check_overlap(room_id, check_in, check_out):
            raise TimeOverlapException
        
        await create_booking(user_id, room_id, check_in, check_out)
        
        if not await set_booking_cache(room_id, check_in, check_out):
            raise CacheException
    except Exception as e:
        raise e
    finally:
        if lock_acquire:
            if not await release_lock(room_id):
                raise ReleaseLockException