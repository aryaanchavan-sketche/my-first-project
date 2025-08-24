import sqlite3
from pathlib import Path
from db_init import DB_PATH , init_db

DRIVERS = [
    ("RAMESH GUPTA", "9876543210", "KA-01-HH-1234"),
    ("SITA DEVI", "9123456780", "KA-01-HH-5678"),
    ("RAHUL KUMAR", "9988776655", "KA-01-HH-9012")
]

if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM drivers;")
    cur.executemany("INSERT INTO drivers(name, phone, lat, lng, vehicle_no, active, trips_completed) VALUES (?, ?, ?, ?, ?, 1, 0);", DRIVERS)
    conn.commit()
    conn.close()
    print("seeded drivers into", DB_PATH)
    
    DRIVERS = [
        ("RAMESH GUPTA", "9876543210", "KA-01-HH-1234"),
    ("SITA DEVI", "9123456780", "KA-01-HH-5678"),
    ("RAHUL KUMAR", "9988776655", "KA-01-HH-9012")
]
    
if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany("INSERT INTO drivers(name, phone, lat, lng, vehicle_no, active, trips_completed) VALUES (?, ?, ?, ?, ?, 1);", DRIVERS)
    conn.commit()
    conn.close()
    print("seeded drivers")
