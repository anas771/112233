import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\user\112233\poultry_data.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find the test batch we just created for سليم شويط
cur.execute("SELECT id FROM batches WHERE batch_num = 'دفعة 1001 (اختبار)' ORDER BY id DESC LIMIT 1")
row = cur.fetchone()
if row:
    batch_id = row['id']
    
    # Calculate farm sales total
    cur.execute("SELECT SUM(total_val), SUM(qty) FROM farm_sales WHERE batch_id=?", (batch_id,))
    f_res = cur.fetchone()
    f_val = f_res[0] or 0
    f_qty = f_res[1] or 0
    
    # Calculate market sales total
    cur.execute("SELECT SUM(net_val), SUM(qty_sold) FROM market_sales WHERE batch_id=?", (batch_id,))
    m_res = cur.fetchone()
    m_val = m_res[0] or 0
    m_qty = m_res[1] or 0
    
    total_rev = f_val + m_val
    total_sold = f_qty + m_qty
    
    # Give it some dummy costs so it's not 100% profit (more realistic)
    total_cost = total_rev * 0.7  # 70% costs
    net_result = total_rev - total_cost
    
    cur.execute("""
        UPDATE batches 
        SET total_rev=?, total_sold=?, total_cost=?, net_result=?, cust_qty=?, cust_val=?, mkt_qty=?, mkt_val=?
        WHERE id=?
    """, (total_rev, total_sold, total_cost, net_result, f_qty, f_val, m_qty, m_val, batch_id))
    
    conn.commit()
    print(f"✅ تم تحديث إجماليات الدفعة #{batch_id} للظهور في لوحة القياس.")
    print(f"   الإيرادات: {total_rev:,.0f} | التكاليف: {total_cost:,.0f} | الصافي: {net_result:,.0f}")

conn.close()
