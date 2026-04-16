import sqlite3
import os
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'poultry_data.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    # Enable WAL mode so web and desktop don't lock each other
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# ----------------- Dashboard -----------------
@app.route('/api/dashboard')
def dashboard():
    conn = get_db()
    tot_batches_row = conn.execute("SELECT COUNT(id) as c FROM batches").fetchone()
    total_batches = tot_batches_row['c'] if tot_batches_row else 0
    profit_row = conn.execute("SELECT SUM(net_result) as p FROM batches").fetchone()
    total_profit = profit_row['p'] if profit_row and profit_row['p'] else 0
    chicks = conn.execute("SELECT SUM(chicks) as ch, SUM(total_dead) as d FROM batches").fetchone()
    total_chicks = chicks['ch'] if chicks and chicks['ch'] else 1 
    total_dead = chicks['d'] if chicks and chicks['d'] else 0
    mortality = round((total_dead / total_chicks) * 100, 2)
    return jsonify({
        "total_batches": total_batches,
        "total_profit": total_profit,
        "total_chicks": chicks['ch'] if chicks['ch'] else 0,
        "mortality": mortality
    })

# ----------------- Batches -----------------
@app.route('/api/batches', methods=['GET', 'POST'])
def batches():
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        conn.execute("""
            INSERT INTO batches (batch_num, warehouse_id, date_in, chicks, net_result, chick_price, chick_val, created_at)
            VALUES (?, ?, ?, ?, 0, 0, 0, datetime('now'))
        """, (data['batch_num'], data['warehouse_id'], data['date_in'], data['chicks']))
        conn.commit()
        return jsonify({"status": "success"})
        
    rows = conn.execute("""
        SELECT b.id, b.batch_num, w.name as warehouse, b.date_in, b.date_out, b.chicks, b.total_dead, b.net_result
        FROM batches b
        LEFT JOIN warehouses w ON b.warehouse_id = w.id
        ORDER BY b.date_in DESC
    """).fetchall()
    return jsonify([dict(r) for r in rows])

# ----------------- Daily Records -----------------
@app.route('/api/batches/<int:batch_id>/daily', methods=['GET', 'POST'])
def daily_records(batch_id):
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        conn.execute("""
            INSERT INTO daily_records (batch_id, rec_date, day_num, dead_count, feed_kg, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(batch_id, rec_date) DO UPDATE SET
                dead_count=excluded.dead_count,
                feed_kg=excluded.feed_kg,
                notes=excluded.notes
        """, (batch_id, data['rec_date'], data['day_num'], data['dead_count'], data['feed_kg'], data.get('notes', '')))
        
        # Update Total Dead in Batches Table
        total_dead = conn.execute("SELECT SUM(dead_count) FROM daily_records WHERE batch_id=?", (batch_id,)).fetchone()[0] or 0
        chicks = conn.execute("SELECT chicks FROM batches WHERE id=?", (batch_id,)).fetchone()[0] or 1
        mort_rate = round((total_dead / chicks) * 100, 2)
        conn.execute("UPDATE batches SET total_dead=?, mort_rate=? WHERE id=?", (total_dead, mort_rate, batch_id))
        conn.commit()
        return jsonify({"status": "success"})

    rows = conn.execute("SELECT * FROM daily_records WHERE batch_id=? ORDER BY rec_date", (batch_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

# ----------------- Warehouses -----------------
@app.route('/api/warehouses', methods=['GET', 'POST'])
def warehouses():
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        conn.execute("INSERT INTO warehouses (name, capacity, location) VALUES (?, ?, ?)", 
                    (data['name'], data['capacity'], data.get('location', '')))
        conn.commit()
        return jsonify({"status": "success"})
        
    rows = conn.execute("SELECT * FROM warehouses ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
