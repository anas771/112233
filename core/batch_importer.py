import openpyxl
import os
import sqlite3
from datetime import datetime

class BatchImporter:
    def __init__(self, db_manager):
        self.db = db_manager

    def build_merged_map(self, ws):
        merged_map = {}
        for m in ws.merged_cells.ranges:
            master_val = ws.cell(m.min_row, m.min_col).value
            for row in range(m.min_row, m.max_row+1):
                for col in range(m.min_col, m.max_col+1):
                    merged_map[(row, col)] = master_val
        return merged_map

    def get_val(self, ws, r, c, merged_map):
        v = ws.cell(r, c).value
        if v is None:
            return merged_map.get((r, c))
        return v

    def resolve_warehouse(self, name):
        wh_name = str(name).strip()
        wh = self.db.fetch_one("SELECT id FROM warehouses WHERE name = ?", (wh_name,))
        if not wh:
            wh_id = self.db.execute("INSERT INTO warehouses (name) VALUES (?)", (wh_name,))
            return wh_id
        return wh['id']

    def import_file(self, file_path):
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, keep_vba=False)
            if 'ورقة1' not in wb.sheetnames:
                return False, f"الورقة 'ورقة1' غير موجودة في {os.path.basename(file_path)}"
            
            ws = wb['ورقة1']
            mm = self.build_merged_map(ws)
            wh_name = self.get_val(ws, 1, 11, mm)
            date_in_raw = self.get_val(ws, 1, 5, mm)
            chicks_count = self.get_val(ws, 1, 2, mm)
            
            if not wh_name or not date_in_raw:
                return False, f"بيانات الرأس ناقصة في {os.path.basename(file_path)}"
            
            date_in = date_in_raw.strftime('%Y-%m-%d') if isinstance(date_in_raw, datetime) else str(date_in_raw).split(' ')[0]
            wh_id = self.resolve_warehouse(wh_name)
            
            # التحقق من وجود دفعة مسبقة بنفس التاريخ والعنبر (Clean & Sync)
            existing = self.db.fetch_one("SELECT id FROM batches WHERE warehouse_id = ? AND date_in = ?", (wh_id, date_in))
            if existing:
                old_id = existing['id']
                self.db.execute("DELETE FROM batches WHERE id = ?", (old_id,))
                self.db.execute("DELETE FROM daily_records WHERE batch_id = ?", (old_id,))
                self.db.execute("DELETE FROM farm_sales WHERE batch_id = ?", (old_id,))
                self.db.execute("DELETE FROM market_sales WHERE batch_id = ?", (old_id,))
                self.db.execute("DELETE FROM batch_cost_records WHERE batch_id = ?", (old_id,))
            
            # 1. السجلات اليومية (ورقة1)
            daily_recs, last_date, total_dead, max_day = [], date_in, 0, 0
            for r in range(5, ws.max_row + 1):
                d_date_raw = self.get_val(ws, r, 1, mm)
                if not d_date_raw: break
                d_date = d_date_raw.strftime('%Y-%m-%d') if isinstance(d_date_raw, datetime) else str(d_date_raw).split(' ')[0]
                d_age = self.get_val(ws, r, 2, mm) or 0
                d_dead = self.get_val(ws, r, 4, mm) or 0
                d_feed = self.get_val(ws, r, 6, mm) or 0
                daily_recs.append({'rec_date': d_date, 'day_num': d_age, 'dead_count': d_dead, 'feed_kg': d_feed * 50})
                last_date, max_day, total_dead = d_date, max(max_day, d_age), total_dead + d_dead

            # 2. المصاريف (اجمالي التكاليف) - الربط الذكي
            detailed_costs = []
            final_summaries = {'feed_val': 0, 'feed_qty': 0, 'chick_val': 0, 'drugs_val': 0, 'gas_val': 0, 'gas_qty': 0, 'sawdust_val': 0, 'sawdust_qty': 0, 'total_cost': 0}
            
            if 'اجمالي التكاليف' in wb.sheetnames:
                ws_c = wb['اجمالي التكاليف']
                # توسيع النطاق إلى 50 صفاً لضمان جلب كافة البيانات كما ظهر في الفيديو
                for r in range(3, 50):
                    name = str(ws_c.cell(r, 1).value or '').strip()
                    # التوقف عند الوصول إلى المجموع النهائي أو صف فارغ تماماً
                    if "الاجمالي" in name or "الإجمالي" in name: 
                        break
                    if not name: 
                        continue
                    
                    qty = ws_c.cell(r, 2).value or 0
                    comp = ws_c.cell(r, 3).value or 0
                    sup = ws_c.cell(r, 4).value or 0
                    total = comp + sup
                    notes = str(ws_c.cell(r, 5).value or '')
                    cat = 'other'
                    if "علف" in name: cat, final_summaries['feed_qty'] = 'feed', final_summaries['feed_qty'] + qty; final_summaries['feed_val'] += total
                    elif "كتاكيت" in name or "صوص" in name: cat = 'chicks'; final_summaries['chick_val'] += total
                    elif "علاج" in name or "أدوية" in name: cat = 'drugs'; final_summaries['drugs_val'] += total
                    elif "غاز" in name: cat, final_summaries['gas_qty'] = 'gas', final_summaries['gas_qty'] + qty; final_summaries['gas_val'] += total
                    elif "نشارة" in name: cat, final_summaries['sawdust_qty'] = 'sawdust', final_summaries['sawdust_qty'] + qty; final_summaries['sawdust_val'] += total
                    detailed_costs.append({'name': name, 'qty': qty, 'comp': comp, 'sup': sup, 'cat': cat, 'notes': notes})
                    final_summaries['total_cost'] += total

            # 3. المبيعات (بيان المبيعات)
            f_sales, m_sales = [], []
            if 'بيان المبيعات' in wb.sheetnames:
                ws_s = wb['بيان المبيعات']
                for r in range(3, 30):
                    cust = ws_s.cell(r, 1).value
                    if not cust: continue
                    f_sales.append({'customer': cust, 'qty': ws_s.cell(r, 2).value or 0, 'price': ws_s.cell(r, 3).value or 0, 'total_val': ws_s.cell(r, 4).value or 0, 'sale_date': last_date})
                for r in range(3, 30):
                    office = ws_s.cell(r, 8).value
                    if not office: continue
                    m_sales.append({'office': office, 'qty_sent': ws_s.cell(r, 9).value or 0, 'deaths': ws_s.cell(r, 10).value or 0, 'qty_sold': ws_s.cell(r, 11).value or 0, 'net_val': ws_s.cell(r, 12).value or 0, 'inv_num': str(ws_s.cell(r, 13).value or '')})

            total_rev = sum(s['total_val'] for s in f_sales) + sum(s['net_val'] for s in m_sales)
            
            # إدخال الدفعة
            batch_id = self.db.execute("""
                INSERT INTO batches (warehouse_id, date_in, date_out, days, chicks, total_dead, 
                                   feed_qty, feed_val, chick_val, gas_qty, gas_val, sawdust_qty, sawdust_val, 
                                   drugs_val, total_cost, total_rev, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (wh_id, date_in, last_date, max_day, chicks_count, total_dead,
                  final_summaries['feed_qty'], final_summaries['feed_val'], final_summaries['chick_val'],
                  final_summaries['gas_qty'], final_summaries['gas_val'], final_summaries['sawdust_qty'], final_summaries['sawdust_val'],
                  final_summaries['drugs_val'], final_summaries['total_cost'], total_rev, datetime.now().isoformat()))
            
            for rec in daily_recs:
                self.db.execute("INSERT OR REPLACE INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg) VALUES (?,?,?,?,?)", (batch_id, rec['rec_date'], rec['day_num'], rec['dead_count'], rec['feed_kg']))
            for s in f_sales:
                self.db.execute("INSERT INTO farm_sales (batch_id, customer, qty, price, total_val, sale_date) VALUES (?,?,?,?,?,?)", (batch_id, s['customer'], s['qty'], s['price'], s['total_val'], s['sale_date']))
            for s in m_sales:
                self.db.execute("INSERT INTO market_sales (batch_id, office, qty_sent, deaths, qty_sold, net_val, inv_num) VALUES (?,?,?,?,?,?,?)", (batch_id, s['office'], s['qty_sent'], s['deaths'], s['qty_sold'], s['net_val'], s['inv_num']))
            for c in detailed_costs:
                self.db.execute("INSERT INTO batch_cost_records (batch_id, cost_name, qty, company_val, supervisor_val, category, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", (batch_id, c['name'], c['qty'], c['comp'], c['sup'], c['cat'], c['notes']))
                
            return True, f"تم استيراد {wh_name} بنجاح (تزامن كامل)"
        except Exception as e:
            return False, f"خطأ في {os.path.basename(file_path)}: {str(e)}"

    def import_folder(self, folder_path):
        results = []
        files = [f for f in os.listdir(folder_path) if f.endswith('.xlsm') and not f.startswith('~$')]
        for f in files:
            full_path = os.path.join(folder_path, f)
            success, msg = self.import_file(full_path)
            results.append({'file': f, 'success': success, 'message': msg})
        return results
