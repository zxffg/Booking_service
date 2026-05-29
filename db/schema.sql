-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS rooms;
-- DROP TABLE IF EXISTS bookings;
-- DROP TYPE IF EXISTS status;

CREATE TABLE IF NOT EXISTS users(
    user_id SERIAL PRIMARY KEY,
    tg_username VARCHAR(40) DEFAULT NULL,
    fullname VARCHAR(50) NOT NULL,
    phone VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS rooms(
    room_id SERIAL PRIMARY KEY,
    name VARCHAR(30),
    description VARCHAR(255),
    max_guests INT    
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