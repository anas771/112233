import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'C:\Users\user\112233\poultry_data.db')
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE name='batches'")
print(cur.fetchone()[0])
conn.close()
