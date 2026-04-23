import os
import sqlite3
from v5.database.connection import DB_URL

print(f"SQLAlchemy URL: {DB_URL}")

# استخراج المسار من URL (حذف sqlite:///)
path = DB_URL.replace("sqlite:///", "")
print(f"Parsed Path: {path}")
print(f"Path exists? {os.path.exists(path)}")

if os.path.exists(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("PRAGMA table_info(warehouses)")
    cols = [col[1] for col in c.fetchall()]
    print(f"Columns in warehouses: {cols}")
    
    c.execute("SELECT COUNT(*) FROM warehouses")
    print(f"Warehouses count: {c.fetchone()[0]}")
    conn.close()
