(function () {
    const $ = (id) => document.getElementById(id);
    const modal = $('modal'), dialog = modal.querySelector('.modal');
    const step1 = $('step1'), step2 = $('step2');
    let source = null; // { type: 'db' | 'file', name: string }

    // Демо-данные автопрофилирования. "!" в конце значения подсвечивает аномалию.
    const PROFILE = [
        ['order_id','int','100%','1','1000'], ['customer_id','int','100%','101','872'],
        ['customer_name','string','98%','-','-'], ['email','string','97%','-','-'],
        ['phone','string','100%','-','-'], ['city','string','98%','-','-'],
        ['product','string','100%','-','-'], ['quantity','int','100%','-3!','500!'],
        ['unit_price','float','100%','50.00','609651!'], ['amount','float','100%','0.00','15000.00'],
        ['order_date','date','100%','05.01.2020','01.12.2030!'], ['ship_date','date','75%!','28.12.2019','15.01.2031!'],
        ['status','string','99%','-','-'], ['age','int','99%','-3!','999!']
    ];

    function renderProfile() {
        $('profileBody').innerHTML = PROFILE.map(row => '<tr>' + row.map(v => {
            const bad = v.endsWith('!');
            return '<td class="' + (bad ? 'bad' : '') + '">' + (bad ? v.slice(0, -1) + ' (!)' : v) + '</td>';
        }).join('') + '</tr>').join('');
    }

    function showStep(n) {
        step1.hidden = n !== 1;
        step2.hidden = n !== 2;
        dialog.classList.toggle('wide', n === 2);
    }

    function resetFile() {
        $('fileInput').value = '';
        $('dropzone').hidden = false;
        $('fileOk').hidden = true;
        $('fileError').hidden = true;
    }

    function open() {
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        $('dbError').hidden = true;
        resetFile();
        showStep(1);
    }
    function close() {
        modal.hidden = true;
        document.body.style.overflow = '';
    }

    $('openCreate').addEventListener('click', open);
    $('modalClose').addEventListener('click', close);
    modal.addEventListener('mousedown', (e) => { if (e.target === modal) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) close(); });

    // Вкладки
    document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t === tab));
        $('panel-db').hidden = tab.dataset.tab !== 'db';
        $('panel-file').hidden = tab.dataset.tab !== 'file';
    }));

    // Подключение к БД (заглушка: замените на запрос к вашему API)
    $('panel-db').addEventListener('submit', (e) => {
        e.preventDefault();
        const ok = ['dbHost', 'dbName', 'dbUser', 'dbPass'].every(id => $(id).value.trim())
            && /^\d{2,5}$/.test($('dbPort').value.trim())
            && $('dbHost').value.trim().toLowerCase() === 'localhost';
        $('dbError').hidden = ok;
        if (!ok) return;
        source = { type: 'db', name: 'raw.' + $('dbName').value.trim() };
        $('tableRow').hidden = false;
        $('metaSource').textContent = source.name;
        showStep(2);
    });

    // Загрузка CSV/XLSX
    function handleFile(file) {
        if (!file) return;
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx'].includes(ext) || file.size > 50 * 1024 * 1024) {
            $('fileError').hidden = false;
            return;
        }
        $('fileError').hidden = true;
        $('dropzone').hidden = true;
        $('fileOk').hidden = false;
        $('fileOkText').textContent = 'Успешно загружен .' + ext + ' файл!';
        const mb = (file.size / 1048576).toFixed(1).replace('.', ',');
        $('fileName').textContent = file.name + ' (' + mb + 'МБ)';
        source = { type: 'file', name: file.name };
    }

    const dz = $('dropzone');
    $('fileInput').addEventListener('change', (e) => handleFile(e.target.files[0]));
    ['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('drag'); }));
    ['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('drag'); }));
    dz.addEventListener('drop', (e) => handleFile(e.dataTransfer.files[0]));
    dz.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('fileInput').click(); } });
    $('fileRemove').addEventListener('click', resetFile);

    $('fileNext').addEventListener('click', () => {
        $('tableRow').hidden = true;
        $('metaSource').textContent = source.name;
        showStep(2);
    });

    $('tableSelect').addEventListener('change', (e) => { $('metaSource').textContent = 'raw.' + e.target.value; });

    $('toRules').addEventListener('click', () => {
        close();
        // TODO: переход на страницу настройки правил, например location.href = 'rules.html';
    });

    renderProfile();
})();