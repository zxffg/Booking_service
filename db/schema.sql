-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS rooms;
-- DROP TABLE IF EXISTS bookings;
-- DROP TYPE IF EXISTS status;

SET search_path TO public;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE IF NOT EXISTS users(
    user_id SERIAL PRIMARY KEY,
    tg_username VARCHAR(40) DEFAULT NULL,
    fullname VARCHAR(50) NOT NULL,
    phone VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS rooms(
    room_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    description VARCHAR(255),
    max_guests INT,
    photo_url VARCHAR(255)    
);

CREATE TYPE status AS ENUM('canceled', 'confirmed', 'pending');
CREATE TABLE IF NOT EXISTS bookings(
    id SERIAL PRIMARY KEY,
    user_id INT,
    room_id iNT,
    accommodation DATERANGE,
    EXCLUDE USING gist (room_id WITH =, accommodation WITH &&),
    status STATUS DEFAULT 'pending',
    craeted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id)
        REFERENCES users(user_id),
    FOREIGN KEY(room_id)
        REFERENCES rooms(room_id)
);

-- Для сиддинга
INSERT INTO rooms(name, description, max_guests, photo_url)
VALUES
    ('Стандарт', 'Компактные (17кв.м), но уютные номера с видом во двор. Есть душевая, гладильная доска и чайник.', 2, 'https://i.pinimg.com/736x/d3/1d/2e/d31d2e25c0ffe5080df86957e1935981.jpg'),
    ('Комфорт', 'Аппартаменты (18кв.м) с Queen size кроватью и небольшим кухонным уголком.', 2, 'https://i.pinimg.com/736x/ff/92/d8/ff92d8384a118b97fac8a270df9cdcb9.jpg'),
    ('Комфорт плюс', 'Номера для тех, кому нужно больше пространства (22кв.м).', 2, 'https://i.pinimg.com/736x/e5/bf/97/e5bf976a7f91826f3d801aae842e9552.jpg'),
    ('Двухуровневая студия', 'Апартаменты со вторым уровнем: просторные двухуровневые студии площадью 30 кв.м.', 4, 'https://i.pinimg.com/736x/65/cf/50/65cf50dd05b096dbd344732bbe9fef5f.jpg'),
    ('Двухуровневые апартаменты с 2 спальнями и террасой', 'Премиальные апартаменты площадью 52 кв.м с элегантным дизайном и продуманной планировкой - две отдельные спальни, кухня-гостиная, второй уровень с полноценными спальными местами и собственная терраса.', 6, 'https://i.pinimg.com/736x/6d/35/e9/6d35e946cd50ab2abdb4b957a02c483f.jpg');