import sys, os, sqlite3, openpyxl
from datetime import date, datetime
import unicodedata

# Reconfigure for UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\user\112233\poultry_data.db'
BASE_DIR = r"C:\Users\user\Desktop"

def _sf(v):
    try: return float(str(v).replace(',','').replace(' ','')) if v not in (None,'','#DIV/0!') else 0.0
    except: return 0.0

def _si(v):
    try: return int(float(str(v).replace(',','').replace(' ',''))) if v not in (None,'','#DIV/0!') else 0
    except: return 0

def clean_name(filename):
    clean = ''.join(c for c in filename if unicodedata.category(c) not in ('Cf',))
    clean = clean.strip()
    for sep in ['دفعة', 'دورة', 'batch', 'Batch']:
        if sep in clean:
            part = clean.split(sep)[0].strip()
            if part: return part
    return clean[:40]

def parse_daily(ws):
    rows = list(ws.iter_rows(values_only=True))
    header_idx = -1
    for i, row in enumerate(rows[:10]):
        flat = " ".join(str(c) for c in row if c is not None)
        if "التاريخ" in flat and ("الوفيات" in flat or "النافق" in flat):
            header_idx = i
            break
    records = []
    if header_idx != -1:
        for row in rows[header_idx+1:]:
            if not row or row[0] is None: continue
            if not hasattr(row[0], "year"): continue
            records.append({
                "date": row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
                "day": _si(row[1]),
                "dead": _si(row[3]),
                "feed": _sf(row[5])
            })
    return records

def parse_sales(ws):
    rows = list(ws.iter_rows(values_only=True))
    data_start = 0
    for i, row in enumerate(rows[:10]):
        flat = " ".join(str(c) for c in row if c is not None)
        if "اسم العميل" in flat or ("العدد" in flat and "السعر" in flat):
            data_start = i + 1
            break
    farm, market = [], []
    SKIP = {"الاجمالي","إجمالي","اجمالي","المجموع","البيان","None","","0"}
    for row in rows[data_start:]:
        if not row or all(c is None for c in row): continue
        n = len(row)
        cust = str(row[0] or "").strip()
        if cust and cust not in SKIP and "#" not in cust:
            q_ajl=_si(row[1]); p_ajl=_sf(row[2]); t_ajl=_sf(row[3])
            q_nqd=_si(row[4]); p_nqd=_sf(row[5]); t_nqd=_sf(row[6])
            if q_ajl>0: farm.append({"customer":cust,"qty":q_ajl,"price":p_ajl,"total":t_ajl or q_ajl*p_ajl})
            if q_nqd>0: farm.append({"customer":cust+" (نقداً)","qty":q_nqd,"price":p_nqd,"total":t_nqd or q_nqd*p_nqd})
        if n > 7:
            office = str(row[7] or "").strip()
            if office and office not in SKIP:
                mq=_si(row[8]); md=_si(row[9]); ms=_si(row[10]); mn=_sf(row[11]); mi=str(row[12] or "")
                if mq>0 or mn>0:
                    market.append({"office":office,"sent":mq,"dead":md,"sold":ms or (mq-md),"net":mn,"inv":mi})
    return farm, market

def parse_summary(ws):
    mapping = [
        (['الكتاكيت', 'عدد الكتاكيت'], 'chicks'),
        (['قيمة الكتاكيت'], 'chick_val'),
        (['قيمة العلف'], 'feed_val'),
        (['أجور نقل'], 'feed_trans'),
        (['العلاجات'], 'drugs_val'),
        (['الغاز'], 'gas_val'),
        (['النشارة'], 'sawdust_val'),
        (['مصاريف عنبر'], 'wh_expenses'),
        (['مصاريف بيت'], 'house_exp'),
        (['تكلفة الماء'], 'water_val'),
        (['صافي الربح'], 'net_result'),
        (['اجمالي المصاريف'], 'total_cost'),
        (['وفيات في العنبر'], 'total_dead'),
    ]
    data = {}
    for row in ws.iter_rows(values_only=True):
        for ci, label in enumerate(row):
            if label is None: continue
            lbl = str(label).strip()
            val = None
            for cv in row[ci+1:]:
                if cv is not None and str(cv) not in ('', '#DIV/0!'):
                    try: val = float(str(cv).replace(',','').replace(' ','')); break
                    except: pass
            for kws, col in mapping:
                if any(kw in lbl for kw in kws):
                    if val is not None and col not in data: data[col] = val
    return data

target_file = None
for root, dirs, files in os.walk(BASE_DIR):
    for f in files:
        if "حسين صادق" in f and f.endswith(".xlsm") and not f.startswith("~$"):
            target_file = os.path.join(root, f)
            break
    if target_file: break

wb = openpyxl.load_workbook(target_file, data_only=True, read_only=True)
daily = parse_daily(wb['ورقة1'])
farm, market = parse_sales(wb['بيان المبيعات'])
summary = parse_summary(wb['اجمالي التكاليف'])

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
wh_name = clean_name(os.path.basename(target_file))
cur.execute("INSERT OR IGNORE INTO warehouses (name) VALUES (?)", (wh_name,))
cur.execute("SELECT id FROM warehouses WHERE name=?", (wh_name,))
wh_id = cur.fetchone()[0]

cur.execute("""INSERT INTO batches 
    (warehouse_id, batch_num, date_in, date_out, chicks, total_dead, total_cost, net_result, created_at) 
    VALUES (?,?,?,?,?,?,?,?,?)""",
    (wh_id, "حسين صادق (اختبار حقيقي)", "2025-12-29", "2026-02-23", 
     summary.get('chicks', 0), summary.get('total_dead', 0), summary.get('total_cost', 0), summary.get('net_result', 0), datetime.now().isoformat()))
bid = cur.lastrowid

for r in daily:
    cur.execute("INSERT INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg) VALUES (?,?,?,?,?)",
               (bid, r['date'][:10], r['day'], r['dead'], r['feed']))
for s in farm:
    cur.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val) VALUES (?,?,?,?,?)",
               (bid, s['customer'], s['qty'], s['price'], s['total']))
for ms in market:
    cur.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)",
               (bid, ms['office'], ms['sent'], ms['dead'], ms['sold'], ms['net'], ms['inv']))

conn.commit()
print(f"DONE_SAVING_BID_{bid}")
conn.close()
