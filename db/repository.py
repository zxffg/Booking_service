from config.database import get_pool
import psycopg

# Создание юзера
async def create_user(tg_username: str, fullname: str, phone: str) -> None:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO users(tg_username, fullname, phone) VALUES(%s, %s, %s);", 
                                  [tg_username, fullname, phone])
                await conn.commit()
        except psycopg.Error as e:
            await conn.rollback()
            raise e

# Получение свободных комнат
async def get_available_rooms(check_in: str, check_out: str) -> list:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT room_id, name, description, max_guests " \
                "FROM rooms WHERE room_id NOT IN "
                "(SELECT room_id FROM bookings WHERE status != 'canceled' AND (daterange(%s, %s) && accommodation));", 
                [check_in, check_out])
                result = await cur.fetchall()
            return result
        except psycopg.Error as e:
            await conn.rollback()
            raise e
        
# Создание брони
async def create_booking(user_id: int, room_id: int, check_in: str, check_out: str) -> None:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO bookings(user_id, room_id, accommodation) VALUES(%s, %s, DATERAGE(%s, %s));", 
                                  [user_id, room_id, check_in, check_out])
                await conn.commit()
        except psycopg.Error as e:
            await conn.rollback()
            raise e
        
# Просмотр броней пользователя
async def get_user_bookings(user_id: int) -> list:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM bookings WHERE user_id = %s ORDER BY id DESC LIMIT 5;", [user_id])
                result = await cur.fetchall()
                return result
        except psycopg.Error as e:
            await conn.rollback()
            raise e

# Отмена брони
async def cancel_booking(id: int) -> None:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE bookings SET status = 'canceled' WHERE id = %s;", [id])
                await conn.commit()
        except psycopg.Error as e:
            await conn.rollback()
            raise e

# Проверка пересечения дат
async def check_overlap(room_id: int, check_in: str, check_out: str) -> bool:
    async with (await get_pool()).connection() as conn:
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1 FROM bookings " \
                "WHERE room_id = %s AND status != 'canceled' AND (DATERANGE(%s, %s) && accommodation)", 
                [room_id, check_in, check_out])
                result = await cur.fetchone()
                return result is not None
        except psycopg.Error as e:
            await conn.rollback()
            raise e