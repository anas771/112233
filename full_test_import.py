import sys, os, sqlite3, openpyxl, glob
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

def parse_sales(ws):
    rows = list(ws.iter_rows(values_only=True))
    data_start = 0
    for i, row in enumerate(rows[:10]):
        flat = " ".join(str(c) for c in row if c is not None)
        if "اسم العميل" in flat or ("العدد" in flat and "السعر" in flat):
            data_start = i + 1
            break
    if data_start == 1:
        flat0 = " ".join(str(c) for c in rows[0] if c is not None)
        if any(kw in flat0 for kw in ["بيان مبيعات", "عنبر", "الفترة"]): data_start = 2

    farm, market = [], []
    SKIP = {"الاجمالي","إجمالي","اجمالي","المجموع","الاجماليات","البيان","بيان","None","","0","اسم العميل"}
    for row in rows[data_start:]:
        if not row or all(c is None for c in row): continue
        n = len(row)
        cust = str(row[0] or "").strip()
        if cust and cust not in SKIP and "#" not in cust:
            q_ajl=_si(row[1] if n>1 else 0); p_ajl=_sf(row[2] if n>2 else 0); t_ajl=_sf(row[3] if n>3 else 0)
            q_nqd=_si(row[4] if n>4 else 0); p_nqd=_sf(row[5] if n>5 else 0); t_nqd=_sf(row[6] if n>6 else 0)
            if q_ajl>0: farm.append({"customer":cust,"qty":q_ajl,"price":p_ajl,"total_val":t_ajl or q_ajl*p_ajl})
            if q_nqd>0: farm.append({"customer":cust+" (نقداً)","qty":q_nqd,"price":p_nqd,"total_val":t_nqd or q_nqd*p_nqd})
        if n > 7:
            office = str(row[7] or "").strip()
            if office and office not in SKIP and "#" not in office:
                mq=_si(row[8] if n>8 else 0); md=_si(row[9] if n>9 else 0)
                ms=_si(row[10] if n>10 else 0); mn=_sf(row[11] if n>11 else 0); mi=str(row[12] or "").strip() if n>12 else ""
                if mq>0 or mn>0:
                    market.append({"office":office,"qty_sent":mq,"deaths":md,"qty_sold":ms or max(0,mq-md),"net_val":mn,"inv_num":mi})
    return farm, market

# Search for the file dynamically
target_file = None
for root, dirs, files in os.walk(BASE_DIR):
    for f in files:
        if "سليم شويط" in f and f.endswith(".xlsm") and not f.startswith("~$"):
            target_file = os.path.join(root, f)
            break
    if target_file: break

if not target_file:
    print("❌ لم يتم العثور على الملف المطلوب (عنبر سليم شويط)")
    sys.exit(1)

print(f"--- اختبار استيراد ملف: {os.path.basename(target_file)} ---")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

wh_name = clean_name(os.path.basename(target_file))
cur.execute("SELECT id FROM warehouses WHERE name=?", (wh_name,))
wh = cur.fetchone()
if not wh:
    cur.execute("INSERT INTO warehouses (name) VALUES (?)", (wh_name,))
    wh_id = cur.lastrowid
else: wh_id = wh[0]

cur.execute("""
    INSERT INTO batches (warehouse_id, batch_num, date_in, date_out, chicks, created_at) 
    VALUES (?, ?, ?, ?, ?, ?)
""", (wh_id, "دفعة 1001 (اختبار)", date.today().isoformat(), date.today().isoformat(), 1000, datetime.now().isoformat()))
batch_id = cur.lastrowid

wb = openpyxl.load_workbook(target_file, data_only=True, read_only=True)
ws_sales = None
for s in wb.sheetnames:
    if 'مبيعات' in s or 'بيان' in s: ws_sales = wb[s]; break

if ws_sales:
    farm, market = parse_sales(ws_sales)
    for s in farm:
        cur.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val) VALUES (?,?,?,?,?)",
                   (batch_id, s['customer'], s['qty'], s['price'], s['total_val']))
    for ms in market:
        cur.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)",
                   (batch_id, ms['office'], ms['qty_sent'], ms['deaths'], ms['qty_sold'], ms['net_val'], ms['inv_num']))
    conn.commit()
    print("✅ تم الاستيراد بنجاح.")

    print("\n📋 مبيعات العنبر المستوردة (أول 5):")
    cur.execute("SELECT * FROM farm_sales WHERE batch_id=? LIMIT 5", (batch_id,))
    for i, r in enumerate(cur.fetchall(), 1):
        print(f"   {i}. {r['customer']} | الكمية: {r['qty']} | السعر: {r['price']}")

    print("\n🏢 مبيعات السوق المستوردة (أول 5):")
    cur.execute("SELECT * FROM market_sales WHERE batch_id=? LIMIT 5", (batch_id,))
    for i, r in enumerate(cur.fetchall(), 1):
        print(f"   {i}. {r['office']} | المرسل: {r['qty_sent']} | الصافي: {r['net_val']}")

else:
    print("❌ خطأ: لم يتم العثور على ورقة مبيعات!")

conn.close()
