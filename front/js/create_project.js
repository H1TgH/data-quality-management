(function () {
    const $ = (id) => document.getElementById(id);
    const modal = $('modal');
    const dialog = modal.querySelector('.modal');
    const step1 = $('step1');
    const step2 = $('step2');
    let uploadedSource = null;
    let selectedFile = null;
    let currentProjectId = null;
    let selectedDbTable = null;

    function showError(element, message) {
        element.textContent = message;
        element.hidden = false;
    }

    function setBusy(button, busy, label) {
        button.disabled = busy;
        if (label) button.textContent = label;
    }

    function escapeHTML(value) {
        return String(value ?? '').replace(/[&<>"']/g, (char) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        })[char]);
    }

    function setSummary(summary) {
        const values = document.querySelectorAll('.analis-content .stat-value');
        if (values.length < 3) return;
        values[0].textContent = summary.active_projects ?? 0;
        values[1].textContent = summary.average_quality_score == null
            ? '—'
            : `${Number(summary.average_quality_score).toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`;
        const attentionValue = values[2].firstChild;
        if (attentionValue && attentionValue.nodeType === Node.TEXT_NODE) {
            attentionValue.nodeValue = `${summary.projects_requiring_attention ?? 0} `;
        } else {
            values[2].prepend(document.createTextNode(`${summary.projects_requiring_attention ?? 0} `));
        }
    }

    function statusText(project) {
        if (!project.last_run_at) return 'Запусков пока нет';
        if (project.errors_count > 0) return 'Ошибки!';
        return project.last_run_status === 'SUCCESS' ? 'Успешно!' : 'Запуск не завершён';
    }

    function renderProjects(items) {
        const container = document.querySelector('.all_project');
        container.replaceChildren();

        for (const project of items) {
            const card = document.createElement('article');
            card.className = 'project-card';
            card.dataset.projectId = project.id;
            const score = project.quality_score;
            const scoreClass = score == null ? '' : score >= 90 ? 'score-good' : score >= 70 ? 'score-mid' : 'score-bad';
            const runDate = project.last_run_at
                ? new Date(project.last_run_at).toLocaleString('ru-RU')
                : '—';
            const statusClass = project.errors_count > 0 ? 'error' : project.last_run_status === 'SUCCESS' ? 'ok' : '';
            card.innerHTML = `
                <button class="card-menu" type="button" aria-label="Действия"></button>
                <h3 class="project-name">${escapeHTML(project.name)}</h3>
                <span class="project-tag">${escapeHTML(project.source_name)}</span>
                <div class="score-row">
                    <span class="small-label">Оценка данных:</span>
                    <span class="score ${scoreClass}">${score == null ? '—' : `${Number(score).toLocaleString('ru-RU')}%`}</span>
                    <span class="arrow"></span>
                </div>
                <div class="run-row">
                    <span class="small-label">Последний запуск:</span>
                    <div><div>${escapeHTML(runDate)}</div><div class="status ${statusClass}">${escapeHTML(statusText(project))}</div></div>
                </div>`;
            card.addEventListener('click', (event) => {
                if (event.target.closest('.card-menu')) return;
                window.location.href = `results.html?project_id=${encodeURIComponent(project.id)}`;
            });
            container.append(card);
        }

        if (!items.length) {
            const empty = document.createElement('p');
            empty.textContent = 'Проектов пока нет. Создайте проект, подключив БД или загрузив файл.';
            container.append(empty);
        }
    }

    async function loadProjects() {
        try {
            const response = await window.api.get('/projects/');
            setSummary(response.summary || {});
            renderProjects(response.items || []);
        } catch (error) {
            const container = document.querySelector('.all_project');
            container.replaceChildren();
            const message = document.createElement('p');
            message.className = 'msg error';
            message.textContent = error.status === 401
                ? 'Войдите в систему, чтобы загрузить проекты.'
                : `Не удалось загрузить проекты: ${error.message}`;
            container.append(message);
        }
    }

    function renderProfile(profile) {
        $('profileBody').replaceChildren();
        for (const column of profile.columns || []) {
            const row = document.createElement('tr');
            const values = [
                column.column_name,
                column.data_type,
                `${Number(column.completeness || 0).toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`,
                column.min_value ?? '—',
                column.max_value ?? '—',
            ];
            for (const value of values) {
                const cell = document.createElement('td');
                cell.textContent = String(value);
                row.append(cell);
            }
            $('profileBody').append(row);
        }
        $('metaRows').textContent = `${profile.total_rows} строк`;
        $('metaColumns').textContent = `${(profile.columns || []).length} полей`;
    }

    async function profileSelectedDbTable() {
        const value = $('tableSelect').value;
        if (!value || !uploadedSource) return;
        const [schemaName, ...tableParts] = value.split('.');
        const tableName = tableParts.join('.');
        if (!tableName) throw new Error('Backend вернул некорректное имя таблицы');

        selectedDbTable = { schemaName, tableName };
        const profile = await window.api.get(
            `/column-profiles/${encodeURIComponent(uploadedSource.sourceId)}`
            + `/tables/${encodeURIComponent(schemaName)}/${encodeURIComponent(tableName)}`,
        );
        renderProfile(profile);
        $('metaSource').textContent = `${schemaName}.${tableName}`;
    }

    function showStep(number) {
        step1.hidden = number !== 1;
        step2.hidden = number !== 2;
        dialog.classList.toggle('wide', number === 2);
    }

    function resetFile() {
        selectedFile = null;
        $('fileInput').value = '';
        $('dropzone').hidden = false;
        $('fileOk').hidden = true;
        $('fileError').hidden = true;
    }

    function open() {
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        $('dbError').hidden = true;
        $('profileError').hidden = true;
        $('fileError').hidden = true;
        $('tableRow').hidden = true;
        uploadedSource = null;
        currentProjectId = null;
        selectedDbTable = null;
        resetFile();
        showStep(1);
    }

    function close() {
        modal.hidden = true;
        document.body.style.overflow = '';
    }

    $('openCreate').addEventListener('click', open);
    $('modalClose').addEventListener('click', close);
    modal.addEventListener('mousedown', (event) => { if (event.target === modal) close(); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !modal.hidden) close(); });

    document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
        $('panel-db').hidden = tab.dataset.tab !== 'db';
        $('panel-file').hidden = tab.dataset.tab !== 'file';
    }));

    $('panel-db').addEventListener('submit', async (event) => {
        event.preventDefault();
        $('dbError').hidden = true;
        $('profileError').hidden = true;
        if ($('dbType').value !== 'PostgreSQL') {
            showError($('dbError'), 'Сейчас поддерживается только PostgreSQL.');
            return;
        }
        const button = $('panel-db').querySelector('button[type="submit"]');
        setBusy(button, true, 'Подключаемся…');
        try {
            const result = await window.api.post('/data-sources/db', {
                host: $('dbHost').value.trim(),
                port: Number($('dbPort').value),
                db_name: $('dbName').value.trim(),
                username: $('dbUser').value.trim(),
                password: $('dbPass').value,
            });
            const tablesResponse = await window.api.get(`/data-sources/${encodeURIComponent(result.source_id)}/tables`);
            const tables = tablesResponse.tables || tablesResponse.tables_full_name || [];
            if (!tables.length) throw new Error('В базе не найдены таблицы');
            uploadedSource = { type: 'db', sourceId: result.source_id };
            const select = $('tableSelect');
            select.replaceChildren(...tables.map((table) => {
                const option = document.createElement('option');
                option.value = table;
                option.textContent = table;
                return option;
            }));
            $('tableRow').hidden = false;
            $('metaSource').textContent = tables[0];
            showStep(2);
            try {
                await profileSelectedDbTable();
            } catch (error) {
                showError($('profileError'), error.message);
            }
        } catch (error) {
            showError($('dbError'), error.message);
        } finally {
            setBusy(button, false, 'Подключиться');
        }
    });

    async function handleFile(file) {
        if (!file) return;
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx', 'xls'].includes(ext) || file.size > 50 * 1024 * 1024) {
            showError($('fileError'), 'Выберите CSV, XLSX или XLS размером до 50 МБ.');
            return;
        }
        selectedFile = file;
        $('fileError').hidden = true;
        $('dropzone').hidden = true;
        $('fileOk').hidden = false;
        $('fileOkText').textContent = 'Файл выбран. Нажмите «Далее», чтобы загрузить его.';
        $('fileName').textContent = `${file.name} (${(file.size / 1048576).toFixed(1).replace('.', ',')} МБ)`;
    }

    $('fileInput').addEventListener('change', (event) => handleFile(event.target.files[0]));
    const dropzone = $('dropzone');
    ['dragenter', 'dragover'].forEach((name) => dropzone.addEventListener(name, (event) => {
        event.preventDefault(); dropzone.classList.add('drag');
    }));
    ['dragleave', 'drop'].forEach((name) => dropzone.addEventListener(name, (event) => {
        event.preventDefault(); dropzone.classList.remove('drag');
    }));
    dropzone.addEventListener('drop', (event) => handleFile(event.dataTransfer.files[0]));
    dropzone.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); $('fileInput').click(); }
    });
    $('fileRemove').addEventListener('click', resetFile);

    $('fileNext').addEventListener('click', async () => {
        if (!selectedFile) return;
        const button = $('fileNext');
        setBusy(button, true, 'Загружаем…');
        $('fileError').hidden = true;
        try {
            const form = new FormData();
            form.append('file', selectedFile);
            const result = await window.api.post('/data-sources/file', form);
            uploadedSource = { type: 'file', sourceId: result.source_id };
            currentProjectId = result.project_id;
            $('metaSource').textContent = result.file_name;
            const profile = await window.api.get(`/column-profiles/${encodeURIComponent(result.source_id)}/file`);
            $('tableRow').hidden = true;
            renderProfile(profile);
            $('profileError').hidden = true;
            showStep(2);
            await loadProjects();
        } catch (error) {
            $('dropzone').hidden = false;
            $('fileOk').hidden = true;
            showError($('fileError'), error.message);
        } finally {
            setBusy(button, false, 'Далее');
        }
    });

    $('tableSelect').addEventListener('change', async () => {
        try {
            await profileSelectedDbTable();
        } catch (error) {
            $('profileBody').replaceChildren();
            showError($('profileError'), error.message);
        }
    });

    $('toRules').addEventListener('click', async () => {
        try {
            if (!currentProjectId && selectedDbTable) {
                const project = await window.api.post('/projects/', {
                    data_source_id: uploadedSource.sourceId,
                    schema_name: selectedDbTable.schemaName,
                    table_name: selectedDbTable.tableName,
                    name: selectedDbTable.tableName,
                });
                currentProjectId = project.project_id;
                await loadProjects();
            }
            if (!currentProjectId) throw new Error('Сначала выберите таблицу или загрузите файл.');
            window.location.href = `front/setting.html?project_id=${encodeURIComponent(currentProjectId)}`;
        } catch (error) {
            showError($('dbError'), error.message);
        }
    });

    loadProjects();
})();
