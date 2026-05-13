// Dilution Lab — app logic (state, rendering, event handling)
// Vanilla JS. No framework. Single source of truth in `state`.

(() => {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const el = (tag, props = {}, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === 'class') e.className = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === 'value') e.value = v;
      else e.setAttribute(k, v);
    }
    for (const c of children) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    return e;
  };

  // ----- Formatters -----
  const fmtMoney = (x) => {
    if (x >= 1e9) return `$${(x/1e9).toFixed(1)}B`;
    if (x >= 1e6) return `$${(x/1e6).toFixed(1)}M`;
    if (x >= 1e3) return `$${(x/1e3).toFixed(0)}K`;
    return `$${Math.round(x).toLocaleString()}`;
  };
  const fmtPct = (x) => `${(x*100).toFixed(2)}%`;
  const fmtNumber = (n) => Number(n).toLocaleString();

  const parseMoney = (s) => {
    if (s == null) return 0;
    let str = String(s).replace(/[\$,\s]/g, '').toUpperCase();
    if (!str) return 0;
    let mult = 1;
    if (str.endsWith('B')) { mult = 1e9; str = str.slice(0,-1); }
    else if (str.endsWith('M')) { mult = 1e6; str = str.slice(0,-1); }
    else if (str.endsWith('K')) { mult = 1e3; str = str.slice(0,-1); }
    const n = parseFloat(str);
    return isFinite(n) ? Math.max(0, Math.round(n * mult)) : 0;
  };

  // ----- State -----
  const state = {
    initialPoolPct: 0.10,
    founders: [],
    rounds: [],
    exitLog: Math.log10(250_000_000),
  };

  // ----- Templates -----
  function loadTemplate() {
    state.initialPoolPct = 0.10;
    state.founders = [
      { name: 'Founder A', pct: 50 },
      { name: 'Founder B', pct: 50 },
    ];
    state.rounds = [
      {
        name: 'Pre-seed', kind: 'SAFE',
        safes: [
          { name: 'Lead Angel', amount: 1_000_000, cap: 10_000_000 },
          { name: 'Operator Angel', amount: 250_000, cap: 8_000_000 },
        ],
        preMoney: 0, raiseAmount: 0, optionPoolPctPost: 0.10, investors: [],
      },
      {
        name: 'Seed', kind: 'PRICED', safes: [],
        preMoney: 20_000_000, raiseAmount: 5_000_000, optionPoolPctPost: 0.12,
        investors: [{ name: 'Seed Lead', amount: 5_000_000 }],
      },
    ];
  }
  function loadBlank() {
    state.initialPoolPct = 0.10;
    state.founders = [{ name: '', pct: 100 }];
    state.rounds = [];
  }
  function loadStacked() {
    state.initialPoolPct = 0.10;
    state.founders = [
      { name: 'CEO', pct: 40 },
      { name: 'CTO', pct: 40 },
      { name: 'Chief Scientist', pct: 20 },
    ];
    state.rounds = [
      {
        name: 'Pre-seed', kind: 'SAFE',
        safes: [
          { name: 'Tier-1 Seed Fund', amount: 1_500_000, cap: 15_000_000 },
          { name: 'Strategic Angel 1', amount: 250_000, cap: 12_000_000 },
          { name: 'Strategic Angel 2', amount: 250_000, cap: 12_000_000 },
          { name: 'Industry Operator', amount: 100_000, cap: 10_000_000 },
        ],
        preMoney: 0, raiseAmount: 0, optionPoolPctPost: 0.10, investors: [],
      },
      {
        name: 'Seed', kind: 'PRICED', safes: [],
        preMoney: 30_000_000, raiseAmount: 10_000_000, optionPoolPctPost: 0.12,
        investors: [{ name: 'Seed Lead VC', amount: 10_000_000 }],
      },
      {
        name: 'Series A', kind: 'PRICED', safes: [],
        preMoney: 80_000_000, raiseAmount: 20_000_000, optionPoolPctPost: 0.15,
        investors: [{ name: 'Series A Lead', amount: 20_000_000 }],
      },
    ];
  }

  // ----- Renderers -----
  function renderFounders() {
    const root = $('#founders-list');
    root.innerHTML = '';
    state.founders.forEach((f, i) => {
      const row = el('div', { class: 'row collapsed-labels' });
      const nameInput = el('input', { type: 'text', placeholder: 'Name', value: f.name });
      nameInput.addEventListener('input', e => { f.name = e.target.value; rerenderDerived(); });
      const pctInput = el('input', { type: 'number', min: '0', max: '100', step: '1', value: String(f.pct) });
      pctInput.addEventListener('input', e => { f.pct = Number(e.target.value) || 0; rerenderDerived(); });
      const nameWrap = el('div', { class: 'field-name' });
      if (i === 0) nameWrap.appendChild(el('label', {}, 'Founder name'));
      nameWrap.appendChild(nameInput);
      const pctWrap = el('div', { class: 'field-pct' });
      if (i === 0) pctWrap.appendChild(el('label', {}, 'Equity %'));
      pctWrap.appendChild(pctInput);
      row.appendChild(nameWrap);
      row.appendChild(pctWrap);
      if (i > 0) {
        const remove = el('button', { class: 'btn-x' }, '✕');
        remove.addEventListener('click', () => { state.founders.splice(i, 1); render(); });
        row.appendChild(el('div', { class: 'actions' }, remove));
      }
      root.appendChild(row);
    });
  }

  function renderRounds() {
    const root = $('#rounds-list');
    root.innerHTML = '';
    state.rounds.forEach((rnd, ri) => {
      const card = el('div', { class: 'round-card' });
      const head = el('div', { class: 'round-head' });
      head.appendChild(el('span', { class: 'badge' }, `Round ${ri+1}`));
      head.appendChild(el('span', { class: 'title' }, `${rnd.name || '(unnamed)'} · ${rnd.kind}`));
      card.appendChild(head);

      // Round name + type row
      const headRow = el('div', { class: 'row' });
      const nameWrap = el('div', { class: 'field-name' });
      nameWrap.appendChild(el('label', {}, 'Round name'));
      const nameI = el('input', { type: 'text', value: rnd.name });
      nameI.addEventListener('input', e => { rnd.name = e.target.value; head.querySelector('.title').textContent = `${rnd.name || '(unnamed)'} · ${rnd.kind}`; });
      nameWrap.appendChild(nameI);

      const typeWrap = el('div', { class: 'field-type' });
      typeWrap.appendChild(el('label', {}, 'Round type'));
      const typeSelect = el('select');
      ['SAFE', 'PRICED'].forEach(k => {
        const o = el('option', { value: k }, k);
        if (rnd.kind === k) o.selected = true;
        typeSelect.appendChild(o);
      });
      typeSelect.addEventListener('change', e => {
        rnd.kind = e.target.value;
        if (rnd.kind === 'SAFE' && (!rnd.safes || rnd.safes.length === 0)) {
          rnd.safes = [{ name: 'Investor', amount: 500_000, cap: 5_000_000 }];
        }
        if (rnd.kind === 'PRICED' && (!rnd.investors || rnd.investors.length === 0)) {
          rnd.investors = [{ name: 'Lead Investor', amount: 3_000_000 }];
          if (!rnd.preMoney) rnd.preMoney = 12_000_000;
          if (!rnd.raiseAmount) rnd.raiseAmount = 3_000_000;
        }
        render();
      });
      typeWrap.appendChild(typeSelect);

      const removeRound = el('button', { class: 'btn-x' }, '✕');
      removeRound.addEventListener('click', () => { state.rounds.splice(ri, 1); render(); });

      headRow.appendChild(nameWrap);
      headRow.appendChild(typeWrap);
      headRow.appendChild(el('div', { class: 'actions' }, removeRound));
      card.appendChild(headRow);

      if (rnd.kind === 'SAFE') {
        card.appendChild(el('div', { class: 'mono-label', style: 'margin-top:14px;' }, 'SAFE notes in this round'));
        rnd.safes.forEach((safe, si) => {
          const r = el('div', { class: si === 0 ? 'row' : 'row collapsed-labels' });
          const n = el('div', { class: 'field-name' });
          if (si === 0) n.appendChild(el('label', {}, 'Investor'));
          const nameI2 = el('input', { type: 'text', value: safe.name });
          nameI2.addEventListener('input', e => { safe.name = e.target.value; });
          n.appendChild(nameI2);
          const a = el('div', { class: 'field-amount' });
          if (si === 0) a.appendChild(el('label', {}, 'Investment ($)'));
          const amtI = makeMoneyInput(safe.amount, v => { safe.amount = v; rerenderDerived(); });
          a.appendChild(amtI);
          const c = el('div', { class: 'field-cap' });
          if (si === 0) c.appendChild(el('label', {}, 'Post-money cap ($)'));
          const capI = makeMoneyInput(safe.cap, v => { safe.cap = v; rerenderDerived(); });
          c.appendChild(capI);
          r.appendChild(n); r.appendChild(a); r.appendChild(c);
          if (rnd.safes.length > 1) {
            const x = el('button', { class: 'btn-x' }, '✕');
            x.addEventListener('click', () => { rnd.safes.splice(si, 1); render(); });
            r.appendChild(el('div', { class: 'actions' }, x));
          }
          card.appendChild(r);
        });
        const addSafe = el('button', { class: 'btn-add', style: 'margin-top:8px;' }, '+ Add SAFE');
        addSafe.addEventListener('click', () => {
          rnd.safes.push({ name: 'Investor', amount: 500_000, cap: 5_000_000 });
          render();
        });
        card.appendChild(addSafe);
      } else {
        // PRICED
        const pricedRow = el('div', { class: 'row', style: 'margin-top:14px;' });
        const preW = el('div', { class: 'field-amount' });
        preW.appendChild(el('label', {}, 'Pre-money ($)'));
        preW.appendChild(makeMoneyInput(rnd.preMoney, v => { rnd.preMoney = v; rerenderDerived(); updateRoundMeta(card, rnd); }));
        const raiseW = el('div', { class: 'field-amount' });
        raiseW.appendChild(el('label', {}, 'Raise ($)'));
        raiseW.appendChild(makeMoneyInput(rnd.raiseAmount, v => { rnd.raiseAmount = v; rerenderDerived(); updateRoundMeta(card, rnd); }));
        const poolW = el('div', { class: 'field-narrow' });
        poolW.appendChild(el('label', {}, 'Pool target (%)'));
        const poolI = el('input', { type: 'number', min: '0', max: '30', step: '1', value: String(rnd.optionPoolPctPost * 100) });
        poolI.addEventListener('input', e => { rnd.optionPoolPctPost = (Number(e.target.value) || 0) / 100; rerenderDerived(); });
        poolW.appendChild(poolI);
        pricedRow.appendChild(preW);
        pricedRow.appendChild(raiseW);
        pricedRow.appendChild(poolW);
        card.appendChild(pricedRow);

        const meta = el('div', { class: 'round-meta' });
        card.appendChild(meta);
        updateRoundMeta(card, rnd);

        card.appendChild(el('div', { class: 'mono-label', style: 'margin-top:6px;' }, 'Investors in this round'));
        rnd.investors.forEach((inv, ii) => {
          const r = el('div', { class: ii === 0 ? 'row' : 'row collapsed-labels' });
          const n = el('div', { class: 'field-name' });
          if (ii === 0) n.appendChild(el('label', {}, 'Investor'));
          const nameI2 = el('input', { type: 'text', value: inv.name });
          nameI2.addEventListener('input', e => { inv.name = e.target.value; });
          n.appendChild(nameI2);
          const a = el('div', { class: 'field-amount' });
          if (ii === 0) a.appendChild(el('label', {}, 'Investment ($)'));
          const amtI = makeMoneyInput(inv.amount, v => { inv.amount = v; rerenderDerived(); });
          a.appendChild(amtI);
          r.appendChild(n); r.appendChild(a);
          if (rnd.investors.length > 1) {
            const x = el('button', { class: 'btn-x' }, '✕');
            x.addEventListener('click', () => { rnd.investors.splice(ii, 1); render(); });
            r.appendChild(el('div', { class: 'actions' }, x));
          }
          card.appendChild(r);
        });
        const addInv = el('button', { class: 'btn-add', style: 'margin-top:8px;' }, '+ Add investor');
        addInv.addEventListener('click', () => {
          rnd.investors.push({ name: 'Co-Lead', amount: 1_000_000 });
          render();
        });
        card.appendChild(addInv);
      }

      root.appendChild(card);
    });
  }

  function updateRoundMeta(card, rnd) {
    let meta = card.querySelector('.round-meta');
    if (!meta) return;
    const post = rnd.preMoney + rnd.raiseAmount;
    const pct = post > 0 ? (rnd.raiseAmount / post * 100).toFixed(1) : '0.0';
    meta.textContent = `POST-MONEY ${fmtMoney(post)} · NEW INVESTOR SHARE ${pct}%`;
  }

  // Money input with on-blur reformatting (commas, M/K/B support)
  function makeMoneyInput(initialValue, onChange) {
    const inp = el('input', { type: 'text', value: initialValue ? fmtNumber(initialValue) : '' });
    inp.addEventListener('blur', () => {
      const v = parseMoney(inp.value);
      inp.value = v ? fmtNumber(v) : '';
      onChange(v);
    });
    inp.addEventListener('input', () => {
      // Live parse without reformat (so user can keep typing)
      onChange(parseMoney(inp.value));
    });
    return inp;
  }

  // ----- Simulation + derived UI -----
  function runSim() {
    const founders = state.founders.filter(f => f.name && f.name.trim() !== '');
    if (founders.length === 0) return null;
    const rounds = state.rounds.map(r => ({
      name: r.name || '(unnamed)',
      kind: r.kind,
      safes: r.kind === 'SAFE' ? r.safes : [],
      preMoney: r.preMoney,
      raiseAmount: r.raiseAmount,
      optionPoolPctPost: r.optionPoolPctPost,
      investors: r.kind === 'PRICED' ? r.investors : [],
    }));
    return CapMath.simulate(founders, state.initialPoolPct, rounds);
  }

  function renderCapTable() {
    const root = $('#cap-table');
    const snaps = runSim();
    if (!snaps) { root.innerHTML = '<p class="muted">Add a founder to get started.</p>'; return; }

    const cols = ['At founding', ...state.rounds.map(r => r.name || '(unnamed)')];
    const allNames = [];
    for (const s of snaps) for (const h of s.holders) if (!allNames.includes(h.name)) allNames.push(h.name);

    const cell = (snap, name) => {
      const h = snap.holders.find(x => x.name === name);
      if (!h) return '<td class="muted">—</td>';
      if (CapMath.isUnconvertedSafe(h)) {
        return `<td><span class="safe-tag">SAFE · ${fmtMoney(h.investment)} @ ${fmtMoney(h.safeCap)}</span></td>`;
      }
      return `<td class="number">${fmtPct(CapMath.holderPercent(snap, h))}</td>`;
    };

    let html = '<table class="dl-table"><thead><tr><th>Holder</th>';
    for (const c of cols) html += `<th class="dl-num">${c}</th>`;
    html += '</tr></thead><tbody>';
    for (const name of allNames) {
      html += `<tr><td class="holder-name">${name}</td>`;
      for (const s of snaps) html += cell(s, name);
      html += '</tr>';
    }
    html += '</tbody></table>';
    root.innerHTML = html;
  }

  function renderWaterfall() {
    const snaps = runSim();
    if (!snaps) return;
    const final = snaps[snaps.length - 1];
    const exitVal = 10 ** state.exitLog;

    $('#exit-bignum').textContent = fmtMoney(exitVal);

    const common = CapMath.waterfallAllCommon(final, exitVal);
    const prefs = CapMath.waterfallWithPrefs(final, exitVal);

    let html = '<table class="dl-table"><thead><tr>'
      + '<th>Holder</th>'
      + '<th class="dl-num">Ownership</th>'
      + '<th class="dl-num">All common</th>'
      + '<th class="dl-num">1× non-part. preferred</th>'
      + '</tr></thead><tbody>';
    for (const h of final.holders) {
      if (CapMath.isUnconvertedSafe(h)) continue;
      const own = fmtPct(CapMath.holderPercent(final, h));
      html += `<tr><td class="holder-name">${h.name}</td>`
        + `<td class="number">${own}</td>`
        + `<td class="number">${fmtMoney(common[h.name] || 0)}</td>`
        + `<td class="number">${fmtMoney(prefs[h.name] || 0)}</td>`
        + '</tr>';
    }
    html += '</tbody></table>';
    $('#waterfall-table').innerHTML = html;

    // Founder takeaways
    const founderNames = state.founders.filter(f => f.name).map(f => f.name);
    const totalPrefs = founderNames.reduce((s, n) => s + (prefs[n] || 0), 0);
    const totalCommon = founderNames.reduce((s, n) => s + (common[n] || 0), 0);
    $('#founders-prefs').textContent = fmtMoney(totalPrefs);
    $('#founders-common').textContent = fmtMoney(totalCommon);
  }

  // Re-render only derived sections (cap table + waterfall)
  function rerenderDerived() {
    renderCapTable();
    renderWaterfall();
  }

  // Full re-render
  function render() {
    $('#initial-pool').value = (state.initialPoolPct * 100).toString();
    renderFounders();
    renderRounds();
    rerenderDerived();
  }

  // ----- Event wiring -----
  function init() {
    loadTemplate();

    $('#initial-pool').addEventListener('input', e => {
      state.initialPoolPct = (Number(e.target.value) || 0) / 100;
      rerenderDerived();
    });

    $('#btn-template').addEventListener('click', () => { loadTemplate(); render(); });
    $('#btn-blank').addEventListener('click', () => { loadBlank(); render(); });
    $('#btn-stacked').addEventListener('click', () => { loadStacked(); render(); });

    $('#btn-add-founder').addEventListener('click', () => {
      state.founders.push({ name: '', pct: 0 });
      render();
    });

    $('#btn-add-safe').addEventListener('click', () => {
      const n = state.rounds.length + 1;
      state.rounds.push({
        name: `Round ${n}`, kind: 'SAFE',
        safes: [{ name: 'Investor', amount: 500_000, cap: 5_000_000 }],
        preMoney: 0, raiseAmount: 0, optionPoolPctPost: 0.10, investors: [],
      });
      render();
    });
    $('#btn-add-priced').addEventListener('click', () => {
      const n = state.rounds.length + 1;
      state.rounds.push({
        name: `Round ${n}`, kind: 'PRICED', safes: [],
        preMoney: 20_000_000, raiseAmount: 5_000_000, optionPoolPctPost: 0.12,
        investors: [{ name: 'Lead', amount: 5_000_000 }],
      });
      render();
    });

    $('#exit-slider').addEventListener('input', e => {
      state.exitLog = Number(e.target.value);
      renderWaterfall();
    });

    render();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
