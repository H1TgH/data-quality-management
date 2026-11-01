/* ================= js/setting_project.js (полная замена файла) ================= */
/* ИСПРАВЛЕНО:
   1. В столбце «Поле» ТЕПЕРЬ ВЕЗДЕ (включая тип «Дубликаты») работает выпадающая
      выборка полей с пунктом «все поля» (выделяет/снимает все поля сразу).
   2. В первой строке («Полные дубликаты») выборка раньше не работала, потому что
      там рисовался статичный текст «все поля» вместо селекта — теперь там
      обычный рабочий мультиселект.
   3. Если отмечены все поля (или пункт «все поля») — сохраняется как ['*']
      и отображается как «все поля». */

/* ================= ДАННЫЕ ================= */
const TYPES = { duplicates: 'Дубликаты', null: 'Null', validation: 'Валидация', dictionary: 'Справочник', range: 'Диапазон', formula: 'Формула' };
const REACTIONS = { auto: 'Автоочистка', indication: 'Индикация' };
const OPERATORS = ['+', '-', '*', '/'];
const CMP = ['=', '>', '<', '>=', '<=', '!='];
const ALL_FIELDS = 'все поля';

const isCleanType = t => t !== 'duplicates' && t !== 'null';

const FIELDS = {
    'raw.orders': ['city', 'email', 'age', 'name', 'phone', 'status', 'amount', 'quantity', 'unit_price', 'order_date', 'ship_date'],
    'raw.amount': ['amount', 'date', 'region', 'manager', 'product_id', 'quantity', 'price'],
    'raw.product': ['product_id', 'name', 'category', 'price', 'stock', 'supplier'],
    'raw.sale': ['sale_id', 'client', 'phone', 'email', 'city', 'amount', 'date']
};
const DICT_VALUES = {
    status: ['new', 'paid', 'shipped', 'delivered', 'cancelled', 'unknown'],
    category: ['electronics', 'clothing', 'food', 'home', 'other'],
    region: ['center', 'north', 'south', 'west'],
    supplier: ['alpha', 'beta', 'gamma'],
    client: ['vip', 'regular', 'new']
};
const DEFAULT_DICT = ['value_1', 'value_2', 'value_3'];

const R = (name, type, fields, params, reaction) => ({ name, type, fields, params, reaction, editing: false });

const projectsRules = {
    'raw.orders': [
        R('Полные дубликаты', 'duplicates', ['*'], null, 'auto'),
        R('Обязательные поля', 'null', ['city', 'email', 'age', 'name'], null, 'auto'),
        R('Валидация email', 'validation', ['email'], '^[\\w.+-]+@[\\w-]+\\.[\\w.]+$', 'indication'),
        R('Маска телефона', 'validation', ['phone'], '^\\+7\\d{10}$', 'indication'),
        R('Справочник статусов', 'dictionary', ['status'], ['new', 'paid', 'shipped', 'delivered', 'cancelled'], 'indication'),
        R('Диапазон возраста', 'range', ['age'], { min: 0, max: 100 }, 'indication')
    ],
    'raw.amount': [
        R('Полные дубликаты', 'duplicates', ['*'], null, 'auto'),
        R('Обязательные поля', 'null', ['amount', 'date', 'manager'], null, 'auto'),
        R('Валидация даты', 'validation', ['date'], '^\\d{4}-\\d{2}-\\d{2}$', 'indication'),
        R('Диапазон суммы', 'range', ['amount'], { min: 0, max: 1000000 }, 'indication'),
        R('Сумма заказа', 'formula', ['quantity', 'price'], { op: '*', cmp: '=', target: 'amount' }, 'indication')
    ],
    'raw.product': [
        R('Полные дубликаты', 'duplicates', ['*'], null, 'auto'),
        R('Обязательные поля', 'null', ['product_id', 'name', 'price'], null, 'auto'),
        R('Диапазон цены', 'range', ['price'], { min: 0, max: 500000 }, 'indication'),
        R('Справочник категорий', 'dictionary', ['category'], ['electronics', 'clothing', 'food'], 'indication'),
        R('Маска артикула', 'validation', ['product_id'], '^[A-Z]{2}\\d{6}$', 'indication'),
        R('Остаток без отрицательных', 'range', ['stock'], { min: 0, max: 100000 }, 'auto'),
        R('Название не пустое', 'validation', ['name'], '^.+$', 'indication')
    ],
    'raw.sale': [
        R('Полные дубликаты', 'duplicates', ['*'], null, 'auto'),
        R('Обязательные поля', 'null', ['client', 'phone', 'amount'], null, 'auto'),
        R('Маска телефона', 'validation', ['phone'], '^\\+7\\d{10}$', 'indication'),
        R('Диапазон суммы', 'range', ['amount'], { min: 0, max: 4000000 }, 'indication')
    ]
};

/* ================= СОСТОЯНИЕ ================= */
let currentKey = null;
let currentCard = null;
let working = [];

const overlay = document.getElementById('rulesOverlay');
const rowsBox = document.getElementById('rulesRows');
const closeBtn = document.getElementById('rulesClose');
const addBtn = document.getElementById('addRule');
const saveBtn = document.getElementById('saveRules');

const el = (tag, cls) => { const d = document.createElement(tag); if (cls) d.className = cls; return d; };
const uniq = arr => [...new Set(arr || [])];
const fieldList = () => uniq(FIELDS[currentKey]);

/* ---------- отображение значений ---------- */
function fieldsText(rule) {
    return rule.fields.includes('*') ? 'все поля' : rule.fields.join(', ');
}
function paramsText(rule) {
    switch (rule.type) {
        case 'duplicates':
        case 'null': return '-';
        case 'validation': return rule.params || '-';
        case 'dictionary': return (rule.params || []).join(', ') || '-';
        case 'range': return 'от ' + rule.params.min + ' до ' + rule.params.max;
        case 'formula': {
            const p = rule.params;
            return rule.fields.join(' ' + p.op + ' ') + ' ' + p.cmp + ' ' + p.target;
        }
    }
    return '-';
}
function reactionText(rule) { return isCleanType(rule.type) ? 'Индикация' : REACTIONS[rule.reaction]; }

/* ---------- мультиселект справочника (параметры) ---------- */
function makeMsel(options, selected, role, multi) {
    const wrap = el('div', 'msel'); wrap.dataset.role = role;
    if (multi) wrap.classList.add('msel--multi');
    const btn = el('button', 'msel__btn'); btn.type = 'button';
    const panel = el('div', 'msel__panel'); panel.hidden = true;
    uniq(options).forEach(v => {
        const lab = el('label', 'msel__opt');
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.value = v; cb.checked = selected.includes(v);
        lab.append(cb, document.createTextNode(' ' + v));
        panel.append(lab);
    });
    const sync = () => {
        btn.textContent = [...panel.querySelectorAll('input:checked')].map(c => c.value).join(', ') || '—';
    };
    sync();
    btn.addEventListener('click', e => {
        e.stopPropagation();
        document.querySelectorAll('.msel__panel:not([hidden])').forEach(p => { if (p !== panel) p.hidden = true; });
        panel.hidden = !panel.hidden;
    });
    panel.addEventListener('click', e => e.stopPropagation());
    panel.addEventListener('change', sync);
    wrap.append(btn, panel);
    return wrap;
}

/* ---------- мультиселект столбца «Поле» с пунктом «все поля» ---------- */
function makeFieldMsel(rule) {
    const list = fieldList();
    const isAll = rule.fields.includes('*');

    const wrap = el('div', 'msel'); wrap.dataset.role = 'fields';
    const btn = el('button', 'msel__btn'); btn.type = 'button';
    const panel = el('div', 'msel__panel'); panel.hidden = true;

    const mkOpt = (v, cls) => {
        const lab = el('label', 'msel__opt' + (cls ? ' ' + cls : ''));
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.value = v;
        lab.append(cb, document.createTextNode(' ' + v));
        panel.append(lab);
        return cb;
    };

    /* первый пункт — «все поля» */
    const allBox = mkOpt(ALL_FIELDS, 'msel__opt--all');
    allBox.checked = isAll;
    const restBoxes = list.map(f => {
        const cb = mkOpt(f);
        cb.checked = isAll || rule.fields.includes(f);
        return cb;
    });

    const sync = () => {
        const checked = restBoxes.filter(c => c.checked);
        allBox.checked = checked.length === restBoxes.length;
        btn.textContent = allBox.checked ? ALL_FIELDS : (checked.map(c => c.value).join(', ') || '—');
    };
    sync();

    panel.addEventListener('change', e => {
        if (e.target === allBox) {
            /* «все поля» выделяет / снимает всё сразу */
            restBoxes.forEach(c => { c.checked = allBox.checked; });
        }
        sync();
    });

    btn.addEventListener('click', e => {
        e.stopPropagation();
        document.querySelectorAll('.msel__panel:not([hidden])').forEach(p => { if (p !== panel) p.hidden = true; });
        panel.hidden = !panel.hidden;
    });
    panel.addEventListener('click', e => e.stopPropagation());

    wrap.append(btn, panel);
    return wrap;
}

/* ---------- чтение выбранного в столбце «Поле» ---------- */
function readFields(row) {
    const boxes = [...row.querySelectorAll('[data-role="fields"] input')];
    if (!boxes.length) return null;
    const allBox = boxes[0];
    const checked = boxes.slice(1).filter(c => c.checked).map(c => c.value);
    if (allBox.checked || (checked.length && checked.length === boxes.length - 1)) return ['*'];
    return checked;
}

/* ---------- конструктор параметров по типу ---------- */
function fieldSelect(val, sub) {
    const s = el('select', 'rule-input formula-sel');
    s.dataset.sub = sub;
    fieldList().forEach(f => s.append(new Option(f, f)));
    s.value = val || (s.options[0] ? s.options[0].value : '');
    return s;
}
function makeParams(rule) {
    const wrap = el('div', 'params-wrap'); wrap.dataset.role = 'params';
    switch (rule.type) {
        case 'duplicates':
        case 'null':
            wrap.innerHTML = '<span class="params-dash">-</span>';
            break;
        case 'validation': {
            const inp = el('input', 'rule-input params-input'); inp.dataset.sub = 'regex';
            inp.value = rule.params || ''; inp.placeholder = 'регулярное выражение';
            wrap.append(inp);
            break;
        }
        case 'dictionary': {
            const vals = DICT_VALUES[rule.fields[0]] || DEFAULT_DICT;
            wrap.append(makeMsel(vals, rule.params || [], 'dict', true));
            break;
        }
        case 'range': {
            const p = rule.params || { min: 0, max: 100 };
            [['от', 'min', p.min], ['до', 'max', p.max]].forEach(([txt, sub, val]) => {
                const l = el('label', 'range-lab'); l.append(document.createTextNode(txt + ' '));
                const i = el('input', 'rule-input range-input'); i.type = 'number'; i.dataset.sub = sub; i.value = val;
                l.append(i); wrap.append(l);
            });
            break;
        }
        case 'formula': {
            const p = (rule.params && rule.params.target !== undefined)
                ? rule.params
                : { op: '*', cmp: '=', target: fieldList()[0] || '' };

            const line = el('div', 'formula-line');

            const opSel = el('select', 'rule-input formula-op');
            opSel.dataset.sub = 'op';
            OPERATORS.forEach(o => opSel.append(new Option(o, o)));
            opSel.value = p.op || '*';

            const cmpSel = el('select', 'rule-input formula-cmp');
            cmpSel.dataset.sub = 'cmp';
            CMP.forEach(o => cmpSel.append(new Option(o, o)));
            cmpSel.value = p.cmp || '=';

            const tSel = fieldSelect(p.target, 'target');

            line.append(opSel, cmpSel, tSel);
            wrap.append(line);
            break;
        }
    }
    return wrap;
}

/* ---------- чтение значений из редактируемой строки ---------- */
function checkedValues(scope, sel) { return [...scope.querySelectorAll(sel + ' input:checked')].map(c => c.value); }
function commitRow(row, rule) {
    const oldType = rule.type;
    rule.name = row.querySelector('[data-role="name"]').value.trim() || rule.name;
    rule.type = row.querySelector('[data-role="type"]').value;

    /* поля читаются ОДИНАКОВО у всех типов (включая «Дубликаты») */
    const f = readFields(row);
    if (f && f.length) rule.fields = f;

    switch (oldType) {
        case 'validation': rule.params = row.querySelector('[data-role="params"] .params-input').value; break;
        case 'dictionary': rule.params = checkedValues(row, '[data-role="dict"]'); break;
        case 'range': rule.params = { min: +row.querySelector('[data-sub="min"]').value || 0, max: +row.querySelector('[data-sub="max"]').value || 0 }; break;
        case 'formula': {
            const q = s => row.querySelector('[data-sub="' + s + '"]');
            rule.params = {
                op: q('op').value || '*',
                cmp: q('cmp').value || '=',
                target: q('target').value || fieldList()[0] || ''
            };
            break;
        }
        default: rule.params = null;
    }
    /* УСЛОВИЕ: для всех типов кроме «Дубликаты» и «Null» реакция всегда «Индикация» */
    rule.reaction = isCleanType(rule.type)
        ? 'indication'
        : row.querySelector('[data-role="reaction"]').value;
}

/* ---------- построение строки ---------- */
function selectFrom(obj, val, role) {
    const s = el('select', 'rule-input'); s.dataset.role = role;
    Object.entries(obj).forEach(([k, v]) => s.append(new Option(v, k)));
    s.value = val;
    return s;
}
function buildRow(rule, i) {
    const row = el('div', 'rule-row'); row.dataset.idx = i;
    const num = el('span', 'rule-num'); num.textContent = (i + 1) + '.';
    const card = el('div', 'rule-card' + (rule.editing ? ' editing' : ''));

    if (!rule.editing) {
        const cN = el('div', 'rule-cell c-name'); cN.textContent = rule.name;
        const cT = el('div', 'rule-cell c-type'); cT.textContent = TYPES[rule.type];
        const cF = el('div', 'rule-cell c-field'); cF.textContent = fieldsText(rule);
        const cP = el('div', 'rule-cell c-params'); cP.textContent = paramsText(rule);
        const cR = el('div', 'rule-cell c-reaction'); cR.textContent = reactionText(rule);
        card.append(cN, cT, cF, cP, cR);
    } else {
        const nameIn = el('input', 'rule-input'); nameIn.dataset.role = 'name'; nameIn.value = rule.name;
        const typeSel = selectFrom(TYPES, rule.type, 'type');

        /* выборка полей с «все поля» — ТЕПЕРЬ У ВСЕХ ТИПОВ, включая первую строку */
        const fieldCell = makeFieldMsel(rule);

        const paramsCell = makeParams(rule);

        let reactCell;
        if (isCleanType(rule.type)) {
            const s = el('select', 'rule-input reaction-locked'); s.dataset.role = 'reaction'; s.disabled = true;
            s.append(new Option('Индикация', 'indication'));
            reactCell = s;
        } else {
            reactCell = selectFrom(REACTIONS, rule.reaction, 'reaction');
        }

        card.append(nameIn, typeSel, fieldCell, paramsCell, reactCell);
        typeSel.addEventListener('change', () => { commitRow(row, rule); render(); });
    }

    /* меню «⋮» + Удалить */
    const menu = el('button', 'rule-menu'); menu.type = 'button'; menu.setAttribute('aria-label', 'Действия');
    const del = el('button', 'rule-delete'); del.type = 'button'; del.textContent = 'Удалить'; del.hidden = true;
    menu.addEventListener('click', e => { e.stopPropagation(); del.hidden = !del.hidden; });
    del.addEventListener('click', e => { e.stopPropagation(); working.splice(i, 1); render(); });
    card.append(menu, del);

    /* двойной клик по свободному месту карточки = вход/выход из конструктора */
    card.addEventListener('dblclick', e => {
        if (e.target.closest('input,select,button,.msel__panel')) return;
        if (rule.editing) { commitRow(row, rule); rule.editing = false; }
        else rule.editing = true;
        render();
    });

    row.append(num, card);
    return row;
}

function render() {
    rowsBox.innerHTML = '';
    working.forEach((rule, i) => rowsBox.append(buildRow(rule, i)));
}

/* ---------- нормализация старых форматов формулы к {op, cmp, target} ---------- */
function normalizeFormula(rule) {
    if (rule.type !== 'formula' || !rule.params) return;
    const p = rule.params;
    if (p.target === undefined) {
        if (p.b !== undefined && p.c !== undefined) {
            rule.fields = [p.b, p.c];
            rule.params = { op: p.op || '*', cmp: p.cmp || '=', target: p.a || rule.fields[0] || '' };
        } else if (p.a !== undefined) {
            rule.fields = [p.a, p.b];
            rule.params = { op: p.op || '*', cmp: '=', target: p.a };
        } else {
            rule.params = { op: '*', cmp: '=', target: rule.fields[0] || '' };
        }
    }
}

/* ---------- открытие / закрытие ---------- */
function openModal(key, card) {
    currentKey = key;
    currentCard = card;
    working = JSON.parse(JSON.stringify(projectsRules[key] || []));
    working.forEach(r => {
        r.editing = false;
        normalizeFormula(r);
        if (isCleanType(r.type)) r.reaction = 'indication';
    });
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    render();
}
function closeModal() {
    overlay.hidden = true;
    document.body.style.overflow = '';
}
function updateCount() {
    if (!currentCard) return;
    const cnt = currentCard.querySelector('.project-card__count');
    if (cnt) cnt.textContent = 'Правил: ' + (projectsRules[currentKey] ? projectsRules[currentKey].length : 0);
}

document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('click', e => {
        e.preventDefault();
        const key = card.dataset.key || (card.querySelector('.project-card__table') || {}).textContent.trim();
        openModal(key, card);
    });
});
closeBtn.addEventListener('click', closeModal);
overlay.addEventListener('mousedown', e => { if (e.target === overlay) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !overlay.hidden) closeModal(); });

/* закрыть все выпадающие панели и пузыри «Удалить» по клику вне */
document.addEventListener('click', () => {
    document.querySelectorAll('.msel__panel:not([hidden])').forEach(p => p.hidden = true);
    document.querySelectorAll('.rule-delete:not([hidden])').forEach(d => d.hidden = true);
});

/* добавить правило — сразу в режиме конструктора */
addBtn.addEventListener('click', () => {
    working.push(R('Новое правило', 'validation', ['*'], '', 'indication'));
    working[working.length - 1].editing = true;
    render();
    rowsBox.lastElementChild.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
});

/* сохранить и применить */
saveBtn.addEventListener('click', () => {
    rowsBox.querySelectorAll('.rule-row').forEach(rowEl => {
        const rule = working[+rowEl.dataset.idx];
        if (rule && rule.editing) commitRow(rowEl, rule);
    });
    projectsRules[currentKey] = working.map(r => {
        const c = Object.assign({}, r);
        delete c.editing;
        if (isCleanType(c.type)) c.reaction = 'indication';
        return c;
    });
    updateCount();
    closeModal();
});