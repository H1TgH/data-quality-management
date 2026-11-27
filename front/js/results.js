(function () {
    const $ = (id) => document.getElementById(id);
    const projectId = new URLSearchParams(location.search).get('project_id');
    const typeInfo = {
        UNIQUENESS: ['Дубликаты', '#D33479'],
        NOT_NULL: ['Обязательное поле', '#F0A030'],
        REGEX: ['Валидация', '#8E5BD0'],
        DICTIONARY: ['Справочник', '#5B82E0'],
        RANGE: ['Диапазон', '#D33479'],
        CUSTOM_SQL: ['Формула', '#F3A6CF'],
    };
    let currentRun = null;
    let currentProject = null;
    let selectedFile = null;

    function toast(message) {
        const element = $('toast');
        element.textContent = message;
        element.hidden = false;
        clearTimeout(toast.timer);
        toast.timer = setTimeout(() => { element.hidden = true; }, 3500);
    }

    function formatPercent(value) {
        return value == null ? '—' : `${Number(value).toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`;
    }

    function setRunMetrics(run) {
        document.querySelector('.score-box b').textContent = formatPercent(run?.quality_score);
        document.querySelector('.mid .box b.green').textContent = run?.rows_total ?? '—';
        document.querySelector('.mid .box b.red').textContent = run?.rows_removed ?? '—';
        $('doneAt').textContent = run?.finished_at
            ? `Проверка завершена · ${new Date(run.finished_at).toLocaleString('ru-RU')}`
            : 'Запусков пока нет';
    }

    function setDonut(groups) {
        const totals = {};
        for (const group of groups) {
            totals[group.rule_type] = (totals[group.rule_type] || 0) + group.rows_count;
        }
        const count = Object.values(totals).reduce((sum, value) => sum + value, 0);
        $('donutTotal').textContent = count;
        if (!count) {
            $('donut').style.background = '#eeeeee';
            $('legend').replaceChildren();
            return;
        }
        let current = 0;
        const parts = Object.entries(totals).map(([type, value]) => {
            const color = typeInfo[type]?.[1] || '#999999';
            const start = current / count * 100;
            current += value;
            return `${color} ${start}% ${current / count * 100}%`;
        });
        $('donut').style.background = `conic-gradient(${parts.join(',')})`;
        $('legend').replaceChildren(...Object.entries(totals).map(([type, value]) => {
            const item = document.createElement('li');
            const dot = document.createElement('i');
            dot.style.background = typeInfo[type]?.[1] || '#999999';
            item.append(dot, document.createTextNode(typeInfo[type]?.[0] || type));
            const total = document.createElement('span');
            total.textContent = `${value} · ${(value / count * 100).toFixed(1).replace('.', ',')}%`;
            item.append(total);
            return item;
        }));
    }

    function expectedText(group) {
        const params = group.expected_condition || {};
        if (group.rule_type === 'RANGE') {
            const min = params.min ?? params.minimum;
            const max = params.max ?? params.maximum;
            if (min != null && max != null) return `от ${min} до ${max}`;
        }
        if (group.rule_type === 'REGEX') return params.value || params.pattern || params.regex || '';
        if (group.rule_type === 'DICTIONARY') {
            const values = params.values || params.allowed_values || params.value;
            if (Array.isArray(values)) return values.join(', ');
        }
        return group.rule_name || '';
    }

    function sqlValue(value) {
        if (value == null) return 'NULL';
        if (Array.isArray(value)) {
            return `ARRAY[${value.map((item) => `'${String(item).replace(/'/g, "''")}'`).join(', ')}]`;
        }
        if (typeof value === 'number') return String(value);
        if (typeof value === 'boolean') return value ? 'TRUE' : 'FALSE';
        return `'${String(value).replace(/'/g, "''")}'`;
    }

    function sqlWithParams(query) {
        return query.sql.replace(/\$(\d+)/g, (placeholder, index) => {
            const value = query.params?.[Number(index) - 1];
            return value === undefined ? placeholder : sqlValue(value);
        });
    }

    async function loadGroupRows(group, container, offset = 0) {
        if (!group.rule_id) {
            container.textContent = 'Правило удалено, детализация недоступна.';
            return;
        }
        const path = `/run/${projectId}/${currentRun.id}/errors/${group.rule_id}/${encodeURIComponent(group.field_name)}?offset=${offset}&limit=50`;
        const response = await window.api.get(path);
        if (!response.items.length) {
            container.textContent = 'Строк с открытыми ошибками нет.';
            return;
        }

        const columns = Object.keys(response.items[0].row_data || {});
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const header = document.createElement('tr');
        header.append(document.createElement('th'));
        for (const column of columns) {
            const th = document.createElement('th');
            th.textContent = column;
            if (column === group.field_name) th.className = 'hl';
            header.append(th);
        }
        thead.append(header);
        const tbody = document.createElement('tbody');
        for (const item of response.items) {
            const row = document.createElement('tr');
            const actionCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.title = 'Пометить строку как валидную';
            checkbox.addEventListener('change', async () => {
                if (!checkbox.checked) return;
                try {
                    await window.api.patch(`/run/${projectId}/${currentRun.id}/errors/${item.id}/valid`);
                    await loadCurrentRun();
                } catch (error) {
                    checkbox.checked = false;
                    toast(error.message);
                }
            });
            actionCell.append(checkbox);
            row.append(actionCell);
            for (const column of columns) {
                const cell = document.createElement('td');
                cell.textContent = item.row_data[column] == null ? '' : String(item.row_data[column]);
                if (column === group.field_name) cell.className = 'hl';
                row.append(cell);
            }
            tbody.append(row);
        }
        table.append(thead, tbody);
        const wrap = document.createElement('div');
        wrap.className = 'detail-wrap';
        wrap.append(table);
        container.replaceChildren(wrap);

        if (response.total > offset + response.items.length) {
            const more = document.createElement('button');
            more.type = 'button';
            more.className = 'ghost';
            more.textContent = 'Показать ещё';
            more.addEventListener('click', () => loadGroupRows(group, container, offset + response.items.length));
            container.append(more);
        }
    }

    function renderGroups(groups) {
        const root = $('errBody');
        root.replaceChildren();
        setDonut(groups);
        for (const group of groups) {
            const info = typeInfo[group.rule_type] || [group.rule_type, '#999999'];
            const item = document.createElement('div');
            item.className = 'item';
            const line = document.createElement('div');
            line.className = 'err-row';
            line.innerHTML = `<button class="field-cell" type="button" aria-expanded="false"></button><span class="tag"></span><span></span><span class="rule"></span><button class="sql-btn" type="button">Сгенерировать SQL</button>`;
            line.querySelector('.field-cell').textContent = group.field_name;
            line.querySelector('.tag').textContent = info[0];
            line.querySelector('.tag').style.color = info[1];
            line.children[2].textContent = group.rows_count;
            line.querySelector('.rule').textContent = group.rule_name || expectedText(group);
            const slot = document.createElement('div');
            slot.className = 'slot';
            line.querySelector('.field-cell').addEventListener('click', async () => {
                const open = item.classList.toggle('open');
                line.querySelector('.field-cell').setAttribute('aria-expanded', String(open));
                if (!open) { slot.replaceChildren(); return; }
                slot.textContent = 'Загружаю строки…';
                try { await loadGroupRows(group, slot); }
                catch (error) { slot.textContent = error.message; }
            });
            line.querySelector('.sql-btn').addEventListener('click', async () => {
                try {
                    const response = await window.api.get(
                        `/run/${projectId}/${currentRun.id}/errors/${group.rule_id}/${encodeURIComponent(group.field_name)}/sql`,
                    );
                    const sql = (response.queries || []).map(sqlWithParams).join('\n');
                    if (!sql) throw new Error('Для этой группы SQL не сформирован.');
                    await navigator.clipboard.writeText(sql);
                    toast('SQL скопирован в буфер обмена');
                } catch (error) { toast(error.message); }
            });
            item.append(line, slot);
            root.append(item);
        }
        if (!groups.length) {
            const empty = document.createElement('p');
            empty.textContent = currentRun ? 'Ошибок нет.' : 'Запустите проверку, чтобы увидеть результаты.';
            root.append(empty);
        }
    }

    async function loadCurrentRun() {
        if (!currentRun) {
            setRunMetrics(null);
            renderGroups([]);
            return;
        }
        currentRun = await window.api.get(`/run/${projectId}/${currentRun.id}`);
        setRunMetrics(currentRun);
        const groups = await window.api.get(`/run/${projectId}/${currentRun.id}/errors`);
        renderGroups(groups);
    }

    async function loadProject() {
        if (!projectId) throw new Error('В ссылке отсутствует project_id. Откройте проект из каталога.');
        const response = await window.api.get('/projects/');
        currentProject = (response.items || []).find((project) => project.id === projectId);
        if (!currentProject) throw new Error('Проект не найден или у вас нет к нему доступа.');
        if (currentProject.source_name.toLowerCase().match(/\.(csv|xls|xlsx)$/)) {
            $('runBtn').textContent = '↓ Загрузить новый файл';
        }
        $('sourceName').textContent = currentProject.source_name;
        document.querySelector('.crumbs span').textContent = currentProject.name;
        document.querySelector('.title-row h1').textContent = `Результаты проверки качества данных`;
        const runs = await window.api.get(`/run/${projectId}`);
        const requestedRunId = new URLSearchParams(location.search).get('run_id');
        currentRun = runs.find((run) => run.id === requestedRunId) || runs[0] || null;
        await loadCurrentRun();
    }

    async function drawChart() {
        const period = $('period').value;
        $('chart').textContent = 'Загружаю историю…';
        try {
            const points = await window.api.get(`/run/${projectId}/analytics?period=${period}`);
            const values = points.map((point) => Number(point.quality_score));
            const labels = points.map((point) => {
                const date = new Date(point.period);
                return period === 'week'
                    ? date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
                    : date.toLocaleDateString('ru-RU', { month: 'short' });
            });
            if (!values.length) { $('chart').textContent = 'За выбранный период запусков нет.'; return; }

            const W = 1100, H = 240, L = 60, R = 40, T = 24, B = 40;
            const min = Math.min(0, Math.floor(Math.min(...values) / 10) * 10);
            const max = Math.max(100, Math.ceil(Math.max(...values) / 10) * 10);
            const x = (index) => L + index * (W - L - R) / Math.max(values.length - 1, 1);
            const y = (value) => T + (max - value) / (max - min || 1) * (H - T - B);
            const pointsString = values.map((value, index) => `${x(index)},${y(value)}`);
            const grid = [0, 50, 100].map((value) => {
                const py = y(value);
                return `<line x1="${L}" x2="${W - R}" y1="${py}" y2="${py}" stroke="#EEE"/><text x="${L - 12}" y="${py + 5}" text-anchor="end" fill="#999" font-size="15">${value}</text>`;
            }).join('');
            const dots = values.map((value, index) => `<circle cx="${x(index)}" cy="${y(value)}" r="4" fill="#D33479"/><text x="${x(index)}" y="${y(value) - 12}" text-anchor="middle" fill="#D33479" font-size="14">${formatPercent(value)}</text><text x="${x(index)}" y="${H - 10}" text-anchor="middle" fill="#888" font-size="15">${labels[index]}</text>`).join('');
            $('chart').innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Динамика качества данных">${grid}<polyline points="${pointsString.join(' ')}" fill="none" stroke="#D33479" stroke-width="3" stroke-linejoin="round"/>${dots}</svg>`;
        } catch (error) { $('chart').textContent = error.message; }
    }

    document.querySelectorAll('.rtab').forEach((tab) => tab.addEventListener('click', () => {
        document.querySelectorAll('.rtab').forEach((item) => item.classList.toggle('active', item === tab));
        $('panel-results').hidden = tab.dataset.panel !== 'results';
        $('panel-trend').hidden = tab.dataset.panel !== 'trend';
        if (tab.dataset.panel === 'trend') drawChart();
    }));
    $('period').addEventListener('change', drawChart);

    $('runBtn').addEventListener('click', async () => {
        if (currentProject && currentProject.source_name.toLowerCase().match(/\.(csv|xls|xlsx)$/)) {
            resetUpload();
            uploadModal.hidden = false;
            return;
        }
        const button = $('runBtn');
        button.disabled = true;
        try {
            const result = await window.api.post(`/run/${projectId}`);
            currentRun = { id: result.run_id };
            await loadCurrentRun();
            toast('Проверка завершена');
        } catch (error) { toast(error.message); }
        finally { button.disabled = false; }
    });

    $('csvBtn').addEventListener('click', async () => {
        if (!currentRun) { toast('Сначала запустите проверку.'); return; }
        try { await window.api.download(`/run/${projectId}/${currentRun.id}/errors.csv`, `run-${currentRun.id}-errors.csv`); }
        catch (error) { toast(error.message); }
    });

    $('publishBtn').addEventListener('click', async () => {
        if (!currentRun) { toast('Сначала запустите проверку.'); return; }
        try {
            const result = await window.api.post(`/run/${projectId}/${currentRun.id}/publish`);
            toast(`Опубликовано: ${result.view_name}`);
        } catch (error) { toast(error.message); }
    });

    $('editRules').addEventListener('click', () => {
        window.location.href = `front/setting.html?project_id=${encodeURIComponent(projectId)}`;
    });

    const uploadModal = $('uploadModal');
    function resetUpload() {
        selectedFile = null;
        $('upInput').value = '';
        $('upStart').hidden = false;
        $('upOk').hidden = true;
        $('upError').hidden = true;
    }
    function handleUploadSelection(file) {
        if (!file) return;
        const extension = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx', 'xls'].includes(extension) || file.size > 50 * 1048576) {
            $('upError').textContent = 'Поддерживаются CSV, XLSX и XLS размером до 50 МБ.';
            $('upError').hidden = false;
            return;
        }
        selectedFile = file;
        $('upStart').hidden = true;
        $('upOk').hidden = false;
        $('upOkText').textContent = `Выбран файл ${file.name}. Загрузка создаст новый проект: отдельной загрузки версии пока нет.`;
        $('upName').textContent = `${file.name} (${(file.size / 1048576).toFixed(1).replace('.', ',')} МБ)`;
    }
    $('runBtn').textContent = '▷ Запустить проверку';
    $('upClose').addEventListener('click', () => { uploadModal.hidden = true; });
    uploadModal.addEventListener('mousedown', (event) => { if (event.target === uploadModal) uploadModal.hidden = true; });
    $('upInput').addEventListener('change', (event) => handleUploadSelection(event.target.files[0]));
    const uploadDrop = $('upDrop');
    ['dragenter', 'dragover'].forEach((name) => uploadDrop.addEventListener(name, (event) => {
        event.preventDefault(); uploadDrop.classList.add('drag');
    }));
    ['dragleave', 'drop'].forEach((name) => uploadDrop.addEventListener(name, (event) => {
        event.preventDefault(); uploadDrop.classList.remove('drag');
    }));
    uploadDrop.addEventListener('drop', (event) => handleUploadSelection(event.dataTransfer.files[0]));
    $('upRun').addEventListener('click', async () => {
        if (!selectedFile) return;
        try {
            const form = new FormData();
            form.append('file', selectedFile);
            const uploaded = await window.api.post('/data-sources/file', form);
            const run = await window.api.post(`/run/${uploaded.project_id}`);
            window.location.href = `results.html?project_id=${encodeURIComponent(uploaded.project_id)}&run_id=${encodeURIComponent(run.run_id)}`;
        } catch (error) { $('upError').textContent = error.message; $('upError').hidden = false; }
    });

    (async () => {
        try { await loadProject(); }
        catch (error) { toast(error.message); }
    })();
})();
