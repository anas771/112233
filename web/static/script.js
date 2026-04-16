let currentBatchId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Theme logic
    const themeBtn = document.getElementById('theme-toggle');
    if (localStorage.getItem('theme') === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
    themeBtn.addEventListener('click', () => {
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            themeBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        }
    });

    // Load initial dashboard
    loadDashboard();
});

function showSection(sec) {
    document.querySelectorAll('.page-section').forEach(el => el.style.display = 'none');
    document.getElementById('sec-' + sec).style.display = 'block';
    
    document.querySelectorAll('.nav-menu a').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    if(sec === 'dashboard') loadDashboard();
    if(sec === 'warehouses') loadWarehouses();
    if(sec === 'batches') loadBatchesFull();
}

function loadDashboard() {
    fetch('/api/dashboard').then(r=>r.json()).then(data => {
        document.getElementById('kpi-batches').textContent = data.total_batches;
        const profitEl = document.getElementById('kpi-profit');
        profitEl.textContent = Number(data.total_profit).toLocaleString();
        if (data.total_profit < 0) profitEl.style.color = 'var(--danger)';
        document.getElementById('kpi-chicks').textContent = Number(data.total_chicks).toLocaleString();
        document.getElementById('kpi-mortality').textContent = data.mortality + '%';
    });

    fetch('/api/batches').then(r=>r.json()).then(data => {
        const tbody = document.getElementById('dash-batches');
        tbody.innerHTML = '';
        data.slice(0, 5).forEach(b => {
            const isLoss = b.net_result < 0;
            const pt = isLoss ? `▼ ${Math.abs(b.net_result).toLocaleString()}` : `▲ ${Number(b.net_result).toLocaleString()}`;
            tbody.innerHTML += `
                <tr>
                    <td>#${b.batch_num}</td>
                    <td>${b.warehouse || 'غير محدد'}</td>
                    <td>${b.date_in}</td>
                    <td>${Number(b.chicks).toLocaleString()}</td>
                    <td>${Number(b.total_dead).toLocaleString()}</td>
                    <td><span class="badge ${isLoss?'loss':'win'}">${pt}</span></td>
                    <td>${b.date_out === 'مستمرة' ? '<span class="badge active">نشطة</span>' : '<span class="badge">مكتملة</span>'}</td>
                </tr>
            `;
        });
    });
}

function loadWarehouses() {
    fetch('/api/warehouses').then(r=>r.json()).then(data => {
        const tbody = document.getElementById('wh-body');
        tbody.innerHTML = '';
        data.forEach(w => {
            tbody.innerHTML += `<tr><td>${w.id}</td><td>${w.name}</td><td>${w.capacity}</td><td>${w.location}</td></tr>`;
        });
    });
}

function addWarehouse() {
    const name = prompt("اسم العنبر:");
    const cap = prompt("السعة الاستيعابية:");
    if(name && cap) {
        fetch('/api/warehouses', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({name: name, capacity: parseInt(cap), location: ''})
        }).then(() => loadWarehouses());
    }
}

function loadBatchesFull() {
    fetch('/api/batches').then(r=>r.json()).then(data => {
        const tbody = document.getElementById('batches-body');
        tbody.innerHTML = '';
        data.forEach(b => {
            tbody.innerHTML += `
                <tr>
                    <td>#${b.batch_num}</td>
                    <td>${b.date_in}</td>
                    <td>${b.chicks}</td>
                    <td><button class="btn btn-outline btn-sm" onclick="viewDaily(${b.id}, '${b.batch_num}')"><i class="fa-solid fa-eye"></i> عرض وتعديل اليوميات</button></td>
                </tr>`;
        });
    });
}

function addBatch() {
    const num = prompt("رقم الدفعة:");
    const chk = prompt("عدد الكتاكيت المستلمة:");
    const wid = prompt("رقم ID للعنبر (ضع 1 مؤقتا):") || 1;
    if(num && chk) {
        const d = new Date().toISOString().split('T')[0];
        fetch('/api/batches', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({batch_num: num, chicks: parseInt(chk), warehouse_id: wid, date_in: d})
        }).then(() => loadBatchesFull());
    }
}

function viewDaily(id, num) {
    document.querySelectorAll('.page-section').forEach(el => el.style.display = 'none');
    document.getElementById('sec-daily').style.display = 'block';
    document.getElementById('did').textContent = num;
    currentBatchId = id;
    
    fetch('/api/batches/'+id+'/daily').then(r=>r.json()).then(data => {
        const tbody = document.getElementById('daily-body');
        tbody.innerHTML = '';
        data.forEach(d => {
            tbody.innerHTML += `<tr><td>${d.rec_date}</td><td>${d.day_num}</td><td>${d.dead_count}</td><td>${d.feed_kg}</td><td>${d.notes}</td></tr>`;
        });
    });
}

function addDaily() {
    const day = prompt("رقم اليوم:");
    const dead = prompt("عدد النفوق:");
    const feed = prompt("كمية العلف (كجم):");
    if(day && dead && feed) {
        const d = new Date().toISOString().split('T')[0];
        fetch('/api/batches/'+currentBatchId+'/daily', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify({rec_date: d, day_num: parseInt(day), dead_count: parseInt(dead), feed_kg: parseFloat(feed), notes: ''})
        }).then(() => viewDaily(currentBatchId, document.getElementById('did').textContent));
    }
}
