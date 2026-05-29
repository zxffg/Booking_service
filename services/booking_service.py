from db.repository import create_booking, check_overlap
from services.redis_service import (acquire_lock, release_lock, set_booking_cache, 
                                    delete_booking_cache, is_room_locked)

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
# Посмотреть через Redis — не занята комната ( is_room_locked)
# Блок постановки ( acquire_lock)
# Посмотреть пересечение даты в Postgres ( check_overlap)
# Записать бронь в Postgres ( create_booking)
# Обновить кэш в Redis ( set_booking_cache)
# Блок снятировки ( release_lock)
async def create_booking_flow(user_id: int, room_id: int, check_in: str, check_out: str) -> None:
    try:
        if await is_room_locked(room_id):
            raise RoomLockedException
        
        if not await acquire_lock(room_id):
            raise AcquireRoomException

        if not await check_overlap(room_id, check_in, check_out):
            raise TimeOverlapException
        
        if not await create_booking(user_id, room_id, check_in, check_out):
            release_lock(room_id)
            raise CreateBookingException
        
        if not await set_booking_cache(room_id, check_in, check_out):
            raise CacheException

        if not await release_lock(room_id):
            raise ReleaseLockException
    except Exception as e:
        raise e