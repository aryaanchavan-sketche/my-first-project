
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS drivers 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    vehicle_no TEXT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1, --1 active, 0 off
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions
 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    amount_paid INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings
 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    user_phone TEXT NOT NULL,
    driver_id INTEGER NOT NULL,
    pickup_lat REAL NOT NULL,
    pickup_lng REAL NOT NULL,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'created', --created/accepted/completed/cancelled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

