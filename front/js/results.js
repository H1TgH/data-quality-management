(function () {
    const $ = (id) => document.getElementById(id);
    const source = new URLSearchParams(location.search).get('source') === 'xlsx' ? 'xlsx' : 'db';
    const SRC_NAME = source === 'xlsx' ? 'primer.xlsx' : 'raw.orders';
    const TABLE = 'raw.orders';

    // ---- Демо-данные (заменить ответом API) ----
    const TYPES = {
        range: ['Диапазон', '#D33479', 't-range'], value: ['Значение', '#F0A030', 't-value'],
        ref: ['Справочник', '#5B82E0', 't-ref'], valid: ['Валидация', '#8E5BD0', 't-valid'], date: ['Дата', '#F3A6CF', 't-date']
    };
    const ERRORS = [
        { f: 'quantity',   t: 'range', n: 40, rule: 'quantity ≥ 0',                sql: `SELECT * FROM ${TABLE} WHERE quantity < 0;` },
        { f: 'amount',     t: 'value', n: 35, rule: 'amount ≥ 0',                  sql: `SELECT * FROM ${TABLE} WHERE amount < 0;` },
        { f: 'email',      t: 'valid', n: 20, rule: 'Корректный формат email',     sql: `SELECT * FROM ${TABLE} WHERE email !~ '^[^@]+@[^@]+\\.[^@]+$';` },
        { f: 'phone',      t: 'valid', n: 2,  rule: 'Корректный формат телефона',  sql: `SELECT * FROM ${TABLE} WHERE phone !~ '^\\+7[0-9 -]{10,}$';` },
        { f: 'order_date', t: 'date',  n: 16, rule: 'Допустимая дата',             sql: `SELECT * FROM ${TABLE} WHERE order_date > CURRENT_DATE;` },
        { f: 'status',     t: 'ref',   n: 40, rule: 'Значение из справочника статусов', sql: `SELECT * FROM ${TABLE} WHERE status NOT IN (SELECT code FROM ref.statuses);` }
    ];
    const COLS = ['order_id','customer_id','customer_name','email','phone','city','product','quantity','unit_price','amount','order_date','ship_date','status','age'];
    const ROWS = [
        [12,'C-012','Анна Иванова','a.ivanova@mail.ru','+7 916 123-45-67','Москва','Роутер',-3,'2 000','-6 000','2026-10-08','2026-10-10','shipped',32],
        [45,'C-045','Иван Петров','i.petrov@mail.ru','+7 921 234-56-78','Казань','Модем',-3,'1 500','-4 500','2026-10-08','2026-10-10','shipped',41],
        [46,'C-045','Иван Петров','i.petrov@mail.ru','+7 921 234-56-78','Казань','Модем',-3,'1 500','-4 500','2026-10-08','2026-10-10','shipped',41],
        [77,'C-045','Иван Петров','i.petrov@mail.ru','+7 921 234-56-78','Казань','Модем',-3,'1 500','-4 500','2026-10-08','2026-10-10','shipped',41],
        [81,'C-045','Иван Петров','i.petrov@mail.ru','+7 921 234-56-78','Казань','Модем',-3,'1 500','-4 500','2026-10-08','2026-10-10','shipped',41]
    ];
    const TREND = {
        weeks:  { labels: ['04.10','05.10','06.10','07.10','08.10','09.10','10.10'], values: [61,67,65,75,79,76,84.7] },
        months: { labels: ['Май','Июн','Июл','Авг','Сен','Окт'], values: [58,64,70,73,78,84.7] }
    };
    const fmt = (v) => String(v).replace('.', ',') + '%';

    // ---- Режим: БД или xlsx ----
    $('sourceName').textContent = SRC_NAME;
    $('runBtn').innerHTML = source === 'xlsx' ? '↓ Загрузить новую версию' : '▷ Запустить проверку';
    $('publishBtn').hidden = source === 'xlsx';

    // ---- Вкладки ----
    document.querySelectorAll('.rtab').forEach(tab => tab.addEventListener('click', () => {
        document.querySelectorAll('.rtab').forEach(t => t.classList.toggle('active', t === tab));
        $('panel-results').hidden = tab.dataset.panel !== 'results';
        $('panel-trend').hidden = tab.dataset.panel !== 'trend';
        if (tab.dataset.panel === 'trend') drawChart();
    }));

    // ---- Круговая диаграмма ----
    const total = ERRORS.reduce((s, e) => s + e.n, 0);
    const byType = {};
    ERRORS.forEach(e => byType[e.t] = (byType[e.t] || 0) + e.n);
    let acc = 0;
    const stops = Object.entries(byType).map(([k, n]) => {
        const from = acc / total * 100; acc += n;
        return `${TYPES[k][1]} ${from}% ${acc / total * 100}%`;
    });
    $('donut').style.background = `conic-gradient(${stops.join(',')})`;
    $('donutTotal').textContent = total;
    $('legend').innerHTML = Object.entries(byType).map(([k, n]) =>
        `<li><i style="background:${TYPES[k][1]}"></i>${TYPES[k][0]}<span>${n} · ${(n / total * 100).toFixed(1).replace('.', ',')}%</span></li>`).join('');

    // ---- Таблица ошибок ----
    function detailHTML(err) {
        const body = ROWS.map((r, i) => '<tr>' + r.map((v, c) => {
            const hl = COLS[c] === err.f ? ' class="hl"' : '';
            return c === 0 ? `<td><input type="checkbox" class="rowchk" data-i="${i}"${i < 4 ? ' checked' : ''}>${v}</td>` : `<td${hl}>${v}</td>`;
        }).join('') + '</tr>').join('');
        const head = COLS.map(c => `<th${c === err.f ? ' class="hl"' : ''}>${c}</th>`).join('');
        return `<div class="detail"><div class="detail-top"><span>Строки с ошибкой</span><span class="sel">Выбрано: ${err.n - 1}</span></div>
            <div class="detail-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div></div>`;
    }
    $('errBody').innerHTML = ERRORS.map((e, i) => `
        <div class="item" data-i="${i}">
            <div class="err-row">
                <button class="field-cell" type="button" aria-expanded="false">${e.f}</button>
                <span class="tag ${TYPES[e.t][2]}">${TYPES[e.t][0]}</span><span>${e.n}</span><span class="rule">${e.rule}</span>
                <button class="sql-btn" type="button">Сгенерировать SQL</button>
            </div><div class="slot"></div>
        </div>`).join('');

    $('errBody').addEventListener('click', (e) => {
        const item = e.target.closest('.item'); if (!item) return;
        const err = ERRORS[item.dataset.i];
        if (e.target.closest('.sql-btn')) {
            (navigator.clipboard ? navigator.clipboard.writeText(err.sql) : Promise.reject()).then(
                () => toast('SQL скопирован в буфер обмена'), () => toast(err.sql));
        } else if (e.target.closest('.field-cell')) {
            const slot = item.querySelector('.slot'), open = item.classList.toggle('open');
            slot.innerHTML = open ? detailHTML(err) : '';
            item.querySelector('.field-cell').setAttribute('aria-expanded', open);
        } else if (e.target.classList.contains('rowchk')) {
            const boxes = [...item.querySelectorAll('.rowchk')];
            item.querySelector('.sel').textContent = 'Выбрано: ' + (err.n - boxes.filter(b => !b.checked).length);
        }
    });
    $('errBody').querySelector('.field-cell').click(); // первая строка раскрыта, как на макете

    // ---- График тренда ----
    function drawChart() {
        const { labels, values } = TREND[$('period').value];
        const W = 1100, H = 240, L = 60, R = 40, T = 24, B = 40, min = 55, max = 90;
        const x = (i) => L + i * (W - L - R) / (values.length - 1);
        const y = (v) => T + (max - v) / (max - min) * (H - T - B);
        const pts = values.map((v, i) => `${x(i)},${y(v)}`);
        const grid = [60, 75, 90].map(g => `<line x1="${L}" x2="${W - R}" y1="${y(g)}" y2="${y(g)}" stroke="#EEE"/><text x="${L - 12}" y="${y(g) + 5}" text-anchor="end" fill="#999" font-size="15">${g}</text>`).join('');
        const dots = values.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="#D33479"/><text x="${x(i)}" y="${y(v) - 12}" text-anchor="middle" fill="#D33479" font-size="14">${fmt(v)}</text><text x="${x(i)}" y="${H - 10}" text-anchor="middle" fill="#888" font-size="15">${labels[i]}</text>`).join('');
        $('chart').innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Динамика качества данных">${grid}
            <polygon points="${x(0)},${y(min)} ${pts.join(' ')} ${x(values.length - 1)},${y(min)}" fill="#D33479" opacity=".06"/>
            <polyline points="${pts.join(' ')}" fill="none" stroke="#D33479" stroke-width="3" stroke-linejoin="round"/>${dots}</svg>`;
    }
    $('period').addEventListener('change', drawChart);

    // ---- Действия ----
    function toast(msg) {
        const t = $('toast'); t.textContent = msg; t.hidden = false;
        clearTimeout(toast.id); toast.id = setTimeout(() => t.hidden = true, 2600);
    }
    function markDone() {
        const d = new Date(), p = (n) => String(n).padStart(2, '0');
        const m = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'][d.getMonth()];
        $('doneAt').textContent = `Проверка завершена · ${d.getDate()} ${m} ${d.getFullYear()}, ${p(d.getHours())}:${p(d.getMinutes())}`;
    }
    $('csvBtn').addEventListener('click', () => {
        const csv = [COLS.join(',')].concat(ROWS.map(r => r.join(','))).join('\n');
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' }));
        a.download = 'quality_errors.csv'; a.click(); URL.revokeObjectURL(a.href);
    });
    $('publishBtn').addEventListener('click', () => toast('Данные опубликованы в Clean Zone')); // TODO: запрос к API
    $('editRules').addEventListener('click', () => toast('Переход к настройке правил')); // TODO: ссылка на страницу правил

    $('runBtn').addEventListener('click', () => {
        if (source === 'xlsx') return openUpload();
        toast('Проверка запущена…'); setTimeout(() => { markDone(); toast('Проверка завершена'); }, 1200); // TODO: API
    });

    // ---- Окно загрузки новой версии ----
    const up = $('uploadModal');
    function resetUpload() { $('upInput').value = ''; $('upStart').hidden = false; $('upOk').hidden = true; $('upError').hidden = true; }
    function openUpload() { resetUpload(); up.hidden = false; }
    function closeUpload() { up.hidden = true; }
    function handleFile(f) {
        if (!f) return;
        const ext = f.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx'].includes(ext) || f.size > 50 * 1048576) { $('upError').hidden = false; return; }
        $('upStart').hidden = true; $('upOk').hidden = false;
        $('upOkText').textContent = `Успешно загружен .${ext} файл!`;
        $('upName').textContent = `${f.name} (${(f.size / 1048576).toFixed(1).replace('.', ',')}МБ)`;
        $('sourceName').textContent = f.name;
    }
    $('upClose').addEventListener('click', closeUpload);
    up.addEventListener('mousedown', (e) => { if (e.target === up) closeUpload(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !up.hidden) closeUpload(); });
    $('upInput').addEventListener('change', (e) => handleFile(e.target.files[0]));
    const dz = $('upDrop');
    ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('drag'); }));
    ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('drag'); }));
    dz.addEventListener('drop', (e) => handleFile(e.dataTransfer.files[0]));
    dz.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('upInput').click(); } });
    $('upRun').addEventListener('click', () => { closeUpload(); toast('Проверка запущена…'); setTimeout(() => { markDone(); toast('Проверка завершена'); }, 1200); });
})();
