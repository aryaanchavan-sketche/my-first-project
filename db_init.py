import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "rikshaw.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    #users
    
    cur.execute(
        
        """CREATE TABLE IF NOT EXISTS users(
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT NOT NULL,
                                        phone TEXT NOT NULL,
                                        subscription_active INTEGER NOT NULL DEFAULT 0);"""
    )
    
#drivers (with leaderboard + movement timestamps)
     
    cur.execute(
        """CREATE TABLE IF NOT EXISTS drivers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    vehicle_no TEXT NOT NULL,
                    
                    active INTEGER NOT NULL DEFAULT 1,
                    trips_completed INTEGER NOT NULL DEFAULT 0,
                    last_update DATETIME DEFAULT CURRENT_TIMESTAMP);"""
    )
    #bookings (supports shared rides, coords, fare, CO2, share token)
    cur.execute(
        """CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            driver_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT "pending",
            shared INTEGER NOT NULL DEFAULT 0,
            start_lat REAL ,
            start_lng REAL,
            end_lat REAL,
            end_lng REAL ,
            fare REAL ,
            co2_emissions REAL,
            share_token TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        );"""
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_drivers_trips ON drivers(trips_completed DESC);")
    
    conn.commit()
    conn.close()

if __name__ =="__main__":
    init_db()
    print("DB initialized at", DB_PATH)

DB_PATH = Path(__file__).parent / "rikshaw.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                subscription_active INTEGER NOT NULL DEFAULT 0
    );''')
    
    cur.execute("""CREATE TABLE IF NOT EXISTS drivers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                lat REAL,
                lng REAL,
                vehicle_no TEXT,
                active INTEGER DEFAULT 1
    );""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                driver_id INTEGER,
                shared INTEGER DEFAULT 0,
                CO2_saved REAL DEFAULT "pending",
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    init_db()
    print("DB initialized.")
