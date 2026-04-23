import sqlite3
import os

def fix_db():
    db_path = r"D:\مجلد جديد\البرنامج حق الدجاج\poultry_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Warehouses
    try:
        cursor.execute("ALTER TABLE warehouses ADD COLUMN capacity INTEGER DEFAULT 0")
        print("ADDED capacity to warehouses")
    except:
        print("Capacity already exists or error")

    # Batches
    try:
        cursor.execute("ALTER TABLE batches ADD COLUMN is_active INTEGER DEFAULT 1")
        print("ADDED is_active to batches")
    except:
        print("is_active already exists or error")

    # Settings
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    
    conn.commit()
    conn.close()
    print("FIX DONE")

if __name__ == "__main__":
    fix_db()
