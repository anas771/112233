import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'C:\Users\user\112233\poultry_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get the last imported batch ID (Hussain Sadiq)
bid_row = cur.execute("SELECT id FROM batches ORDER BY id DESC LIMIT 1").fetchone()
if not bid_row:
    print('No data found.')
    sys.exit()
bid = bid_row['id']

print(f'\n=== محتويات الجداول للدفعة رقم #{bid} (حسين صادق) ===')

print('\n🍗 [جدول farm_sales] - مبيعات العنبر (أول 5 سجلات):')
rows = cur.execute("SELECT customer, qty, price, total_val FROM farm_sales WHERE batch_id=? LIMIT 5", (bid,)).fetchall()
for r in rows:
    print(f'   - العميل: {r["customer"]:15} | الكمية: {r["qty"]:4} | السعر: {r["price"]:4} | الإجمالي: {r["total_val"]:,.0f}')

print('\n🏢 [جدول market_sales] - مبيعات السوق:')
market_rows = cur.execute("SELECT office, qty_sent, qty_sold, net_val FROM market_sales WHERE batch_id=?", (bid,)).fetchall()
for r in market_rows:
    print(f'   - المكتب: {r["office"]:15} | مرسل: {r["qty_sent"]:4} | مباع: {r["qty_sold"]:4} | الصافي: {r["net_val"]:,.0f}')

print('\n📅 [جدول daily_records] - السجلات اليومية (أول 5 أيام):')
daily_rows = cur.execute("SELECT rec_date, day_num, dead_count, feed_kg FROM daily_records WHERE batch_id=? LIMIT 5", (bid,)).fetchall()
for r in daily_rows:
    print(f'   - التاريخ: {r["rec_date"]} | اليوم: {r["day_num"]:2} | النافق: {r["dead_count"]:2} | العلف: {r["feed_kg"]:4} كيس')

conn.close()
