DROP TABLE IF EXISTS ad_videos;
DROP TABLE IF EXISTS ad_images;
DROP TABLE IF EXISTS ads;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    picture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    age INTEGER NOT NULL,
    country TEXT NOT NULL,
    department TEXT NOT NULL,
    city TEXT NOT NULL,
    whatsapp TEXT NOT NULL,
    phone TEXT,
    telegram TEXT,
    category_id INTEGER,
    status TEXT DEFAULT 'activo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE ad_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    filename TEXT NOT NULL,
    FOREIGN KEY (ad_id) REFERENCES ads (id)
);

CREATE TABLE ad_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    filename TEXT NOT NULL,
    FOREIGN KEY (ad_id) REFERENCES ads (id)
);