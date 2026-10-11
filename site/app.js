// Game Style Icons landing page: one booklet, re-inked in the world you pick.
import data from './data.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const STYLES = data.styles;
const BY = Object.fromEntries(STYLES.map((s) => [s.slug, s]));
const ICONS = data.icons;
const REPO = 'https://github.com/horlesq/game-style-icons';
const CDN = `https://cdn.jsdelivr.net/npm/game-style-icons@${data.version.split('.')[0]}`;
const SIZES = [16, 24, 32, 48, 64, 96, 128];
const STACKS = ['element', 'react', 'string', 'svg'];
const reduced = matchMedia('(prefers-reduced-motion: reduce)');

const store = {
  get(k, d) { try { return localStorage.getItem('gsi-' + k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('gsi-' + k, v); } catch { /* private mode: not remembered */ } },
};
const state = {
  world: BY[store.get('world')] ? store.get('world') : 'super-mario',
  item: ICONS.includes(store.get('item')) ? store.get('item') : 'sword',
  stack: STACKS.includes(store.get('stack')) ? store.get('stack') : 'element',
  size: 64,
  paper: false,
};

const pascal = (s) => s.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join('');
const label = (n) => n.replace(/-/g, ' ');
const comp = (slug, name) => BY[slug].prefix + pascal(name);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const svgUrl = (slug, name) => `svg/${slug}/${name}.svg`;

// ---------- icons: <img> for most worlds, inline SVG for the two that draw in currentColor
const svgText = new Map();
function fetchSvg(slug, name) {
  const key = slug + '/' + name;
  if (!svgText.has(key)) svgText.set(key, fetch(svgUrl(slug, name)).then((r) => (r.ok ? r.text() : '')).catch(() => ''));
  return svgText.get(key);
}
let uid = 0;
function paint(el, slug, name, alt = '') {
  el.dataset.s = slug; el.dataset.n = name;
  if (BY[slug].inline) {
    const want = slug + '/' + name;
    fetchSvg(slug, name).then((t) => {
      if (el.dataset.s + '/' + el.dataset.n !== want) return;
      const id = 'p' + (++uid).toString(36);
      el.innerHTML = t.replace(/ width="24" height="24"/, '').replace(/<title>.*?<\/title>/, '').replace(/gsi-[a-z0-9-]+/g, (m) => m + '-' + id);
      const svg = el.querySelector('svg');
      if (svg) { svg.setAttribute('aria-hidden', alt ? 'false' : 'true'); if (!alt) svg.removeAttribute('role'); }
    });
  } else {
    let img = el.firstElementChild;
    if (!img || img.tagName !== 'IMG') { el.innerHTML = ''; img = document.createElement('img'); img.decoding = 'async'; img.loading = 'lazy'; el.append(img); }
    img.alt = alt; img.src = svgUrl(slug, name);
  }
}
function ic(slug, name, alt = '') {
  const el = document.createElement('span');
  el.className = 'ic';
  paint(el, slug, name, alt);
  return el;
}

// ---------- code samples for each stack
function code(stack, slug, name, size) {
  const C = comp(slug, name);
  switch (stack) {
    case 'react': return `import { ${C} } from 'game-style-icons/${slug}';\n\n<${C} size={${size}} />`;
    case 'string': return `import { ${C} } from 'game-style-icons/html/${slug}';\n\nel.innerHTML = ${C}({ size: ${size} });`;
    case 'svg': return `<img src="${CDN}/svg/${slug}/${name}.svg"\n     width="${size}" height="${size}" alt="${label(name)}">`;
    default: return `<script type="module">import 'game-style-icons/element';</script>\n\n<game-icon set="${slug}" name="${name}" size="${size}"></game-icon>`;
  }
}
const STACK_NOTE = {
  element: 'A standard web component: plain HTML, Vue, Svelte, Angular, Astro, anything that renders HTML. From a CDN, the script tag is the whole install.',
  react: 'React components (React 18+) with size and title props, a forwarded ref and TypeScript types.',
  string: 'Functions that return the SVG as a string: server templates, v-html, {@html}, innerHTML. Each call gets its own ids.',
  svg: 'Plain .svg files for <img>, CSS backgrounds or design tools. Also in the package under svg/<world>/<item>.svg.',
};
function highlight(src) {
  return esc(src)
    .replace(/(&lt;\/?)([a-zA-Z-]+)/g, '$1<span class="tk-t">$2</span>')
    .replace(/\b(import|from|export)\b/g, '<span class="tk-k">$1</span>')
    .replace(/('[^'\n]*'|&quot;[^\n]*?&quot;)/g, '<span class="tk-s">$1</span>');
}
function setCode(key, src) {
  const el = $(`[data-code="${key}"]`);
  if (el) { el.innerHTML = highlight(src); el.dataset.raw = src; }
}

// ---------- copy with feedback
const announce = (msg) => { const a = $('[data-announce]'); a.textContent = ''; requestAnimationFrame(() => { a.textContent = msg; }); };
async function copy(text, btn, done = 'Copied') {
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch {
    const t = document.createElement('textarea'); t.value = text; t.setAttribute('readonly', ''); t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.append(t); t.select(); try { ok = document.execCommand('copy'); } catch { ok = false; } t.remove();
  }
  const lab = btn && $('[data-label]', btn);
  if (lab) {
    const was = lab.dataset.was || lab.textContent; lab.dataset.was = was;
    lab.textContent = ok ? done : 'Press Ctrl+C';
    clearTimeout(btn._t); btn._t = setTimeout(() => { lab.textContent = was; }, 1600);
  }
  announce(ok ? done : 'Copy failed. Select the text and copy it yourself.');
  return ok;
}

// ---------- cover: install slot and the stepping item box
const INSTALL = { npm: 'npm install game-style-icons', cdn: `<script type="module" src="${CDN}/src/element.js"></script>` };
let installTab = 'npm';
$$('[data-install-tab]').forEach((b) => b.addEventListener('click', () => {
  installTab = b.dataset.installTab;
  $$('[data-install-tab]').forEach((x) => x.setAttribute('aria-selected', String(x === b)));
  $('[data-install-code]').textContent = INSTALL[installTab];
}));
$('[data-copy-install]').addEventListener('click', (e) => copy(INSTALL[installTab], e.currentTarget, 'Copied'));

const coverIcon = $('[data-cover-icon]');
let coverIdx = Math.max(0, STYLES.findIndex((s) => s.slug === state.world));
let coverTimer = null, coverPaused = false, coverHeld = false;
const coverItem = 'sword';
STYLES.forEach((s) => { if (!s.inline) { const i = new Image(); i.src = svgUrl(s.slug, coverItem); } });
function showCover() {
  const s = STYLES[coverIdx];
  paint(coverIcon, s.slug, coverItem, `${label(coverItem)} in the ${s.title} style`);
  $('[data-cover-level]').textContent = `${s.world}-${s.level}`;
  $('[data-cover-name]').textContent = s.title;
}
function tick() { if (!coverPaused && !coverHeld) { coverIdx = (coverIdx + 1) % STYLES.length; showCover(); } }
function startCover() { clearInterval(coverTimer); if (!reduced.matches && !coverPaused) coverTimer = setInterval(tick, 1400); }
const pauseBtn = $('[data-cover-pause]');
function setPaused(p) { coverPaused = p; pauseBtn.setAttribute('aria-pressed', String(p)); pauseBtn.textContent = p ? 'Play' : 'Pause'; startCover(); }
pauseBtn.addEventListener('click', () => setPaused(!coverPaused));
const itembox = $('.itembox');
itembox.addEventListener('pointerenter', () => { coverHeld = true; });
itembox.addEventListener('pointerleave', () => { coverHeld = false; });
itembox.addEventListener('focusin', () => { coverHeld = true; });
itembox.addEventListener('focusout', () => { coverHeld = false; });
$$('[data-cover-use]').forEach((b) => b.addEventListener('click', () => setWorld(STYLES[coverIdx].slug)));
if (reduced.matches) setPaused(true);
reduced.addEventListener?.('change', () => { if (reduced.matches) setPaused(true); });

// ---------- worlds list
function buildWorlds() {
  const host = $('[data-worlds]');
  const frag = document.createDocumentFragment();
  data.worlds.forEach((wname, wi) => {
    const head = document.createElement('div');
    head.className = 'world-head';
    head.innerHTML = `<span>World ${wi + 1}</span><h3>${esc(wname)}</h3>`;
    frag.append(head);
    STYLES.filter((s) => s.world === wi + 1).forEach((s) => {
      const row = document.createElement('label');
      row.className = 'level'; row.dataset.slug = s.slug;
      row.innerHTML = `<input type="radio" name="world" value="${s.slug}"><span class="level-no">${s.world}-${s.level}</span>`
        + `<span class="level-text"><span class="level-name">${esc(s.title)}</span><span class="level-look">${esc(s.look)}</span>`
        + `<span class="level-flag"><span class="ui-icon" data-icon="flag"></span>Your world</span></span><span class="level-strip"></span>`;
      const strip = $('.level-strip', row);
      ['heart', 'sword', 'potion', 'chest', 'gamepad'].forEach((n) => strip.append(ic(s.slug, n)));
      $('input', row).addEventListener('change', () => setWorld(s.slug));
      frag.append(row);
    });
  });
  host.append(frag);
}

// ---------- items list and the item card
function buildItems() {
  const host = $('[data-groups]');
  data.groups.forEach(([title, names]) => {
    const g = document.createElement('section');
    g.className = 'group'; g.dataset.group = title;
    g.innerHTML = `<h3>${esc(title)} <span>${names.length}</span></h3><div class="grid-items"></div>`;
    const grid = $('.grid-items', g);
    names.forEach((n) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'item'; b.dataset.item = n; b.setAttribute('aria-pressed', 'false');
      b.append(ic(state.world, n));
      b.append(Object.assign(document.createElement('span'), { textContent: label(n) }));
      b.addEventListener('click', () => { setItem(n); if (matchMedia('(max-width: 1080px)').matches) $('[data-card]').scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth', block: 'start' }); });
      grid.append(b);
    });
    host.append(g);
  });
  const every = $('[data-every]');
  STYLES.forEach((s) => {
    const b = document.createElement('button');
    b.type = 'button'; b.dataset.slug = s.slug; b.title = s.title; b.setAttribute('aria-label', `${s.title}: use this world`);
    b.append(ic(s.slug, state.item));
    b.addEventListener('click', () => setWorld(s.slug));
    every.append(b);
  });
}
const find = $('[data-find]');
function filter() {
  const q = find.value.trim().toLowerCase().replace(/\s+/g, '-');
  let shown = 0;
  $$('.item').forEach((b) => { const hit = !q || b.dataset.item.includes(q); b.hidden = !hit; if (hit) shown++; });
  $$('.group').forEach((g) => { g.hidden = !$$('.item', g).some((b) => !b.hidden); });
  $('[data-find-empty]').hidden = shown > 0;
}
find.addEventListener('input', filter);
$$('[data-find-try]').forEach((b) => b.addEventListener('click', () => { find.value = b.dataset.findTry; filter(); find.focus(); }));

function drawGrid() {
  const svg = $('[data-card-grid]');
  const s = BY[state.world];
  const vb = { minecraft: 16, pokemon: 16, undertale: 16, tetris: 12, 'space-invaders': 13 }[s.slug];
  const n = vb || 24, off = vb ? 0 : -1, span = vb || 26;
  svg.setAttribute('viewBox', `${off} ${off} ${span} ${span}`);
  let lines = '';
  for (let k = 0; k <= n; k++) {
    const major = vb ? k % 4 === 0 : k % 4 === 0;
    lines += `<line x1="${k}" y1="0" x2="${k}" y2="${n}" class="${major ? 'major' : ''}"/><line x1="0" y1="${k}" x2="${n}" y2="${k}" class="${major ? 'major' : ''}"/>`;
  }
  svg.innerHTML = lines;
}
$('[data-grid-toggle]').addEventListener('change', (e) => $('[data-card-grid]').classList.toggle('on', e.target.checked));

function renderCard() {
  const { world: w, item: n } = state;
  $('[data-card-title]').textContent = label(n);
  $('[data-card-comp]').textContent = comp(w, n);
  paint($('[data-card-icon]'), w, n, `${label(n)}, ${BY[w].title} style`);
  const dark = $('[data-card-dark]');
  dark.replaceChildren(ic(w, n));
  setCode('card', code(state.stack, w, n, 32));
  const dl = $('[data-download]');
  dl.href = svgUrl(w, n); dl.setAttribute('download', `${w}-${n}.svg`);
  $$('.item').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.item === n)));
  $$('[data-every] button').forEach((b) => { paint($('.ic', b), b.dataset.slug, n); b.setAttribute('aria-pressed', String(b.dataset.slug === w)); });
  drawGrid();
}
$('[data-copy-svg]').addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const t = await fetchSvg(state.world, state.item);
  copy(t.trim(), btn, 'SVG copied');
});

// ---------- getting started and controls
function renderStart() {
  const { world: w, stack } = state;
  setCode('start', code(stack, w, state.item, 48));
  $('[data-stack-note]').textContent = STACK_NOTE[stack];
  $$('[data-stack]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.stack === stack)));
  const scr = $('[data-start-screen]');
  scr.replaceChildren(...['heart', state.item, 'coin', 'chest', 'save'].filter((v, i, a) => a.indexOf(v) === i).slice(0, 5).map((n) => ic(w, n)));
  $('[data-start-caption]').textContent = `The ${BY[w].title} world on a dark screen. Same names in every stack: ${comp(w, state.item)}.`;
}
$$('[data-stack]').forEach((b) => b.addEventListener('click', () => setStack(b.dataset.stack)));
$$('[data-stack]').forEach((b) => b.addEventListener('keydown', (e) => {
  if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
  const i = (STACKS.indexOf(state.stack) + (e.key === 'ArrowRight' ? 1 : STACKS.length - 1)) % STACKS.length;
  setStack(STACKS[i]); $(`[data-stack="${STACKS[i]}"]`).focus();
}));
function setStack(s) { state.stack = s; store.set('stack', s); renderStart(); renderPad(); renderCard(); }

function renderPad() {
  const { world: w, item: n, size } = state;
  const el = $('[data-pad-icon]');
  el.setAttribute('set', w); el.setAttribute('name', n); el.setAttribute('size', String(size));
  $('[data-pad-screen]').classList.toggle('paper', state.paper);
  const s = BY[w];
  $('[data-pad-caption]').textContent = `World ${s.world}-${s.level}, ${s.title}: ${label(n)} at ${size} px on a ${state.paper ? 'paper' : 'dark'} screen.`;
  setCode('pad', code(state.stack, w, n, size));
}
const pad = $('[data-pad]');
function press(act) {
  const hit = $(`[data-pad-act="${act}"]`);
  if (hit) { hit.classList.add('hit'); setTimeout(() => hit.classList.remove('hit'), 140); }
  const i = STYLES.findIndex((s) => s.slug === state.world);
  const status = $('[data-pad-status]');
  if (act === 'left' || act === 'right') { setWorld(STYLES[(i + (act === 'right' ? 1 : STYLES.length - 1)) % STYLES.length].slug); status.textContent = `World: ${BY[state.world].title}`; }
  if (act === 'up' || act === 'down') {
    const k = SIZES.indexOf(state.size);
    state.size = SIZES[Math.min(SIZES.length - 1, Math.max(0, k + (act === 'up' ? 1 : -1)))];
    renderPad(); status.textContent = `Size: ${state.size} px`;
  }
  if (act === 'a') copy($('[data-code="pad"]').dataset.raw, null, 'Code copied').then((ok) => { status.textContent = ok ? 'Code copied' : 'Copy failed'; });
  if (act === 'b') { setItem(ICONS[(ICONS.indexOf(state.item) + 1) % ICONS.length]); status.textContent = `Item: ${label(state.item)}`; }
  if (act === 'select') { setStack(STACKS[(STACKS.indexOf(state.stack) + 1) % STACKS.length]); status.textContent = `Stack: ${$(`[data-stack="${state.stack}"]`).textContent}`; }
  if (act === 'start') { state.paper = !state.paper; renderPad(); status.textContent = state.paper ? 'Paper screen' : 'Dark screen'; }
}
$$('[data-pad-act]').forEach((b) => b.addEventListener('click', () => press(b.dataset.padAct)));
pad.addEventListener('keydown', (e) => {
  const map = { ArrowLeft: 'left', ArrowRight: 'right', ArrowUp: 'up', ArrowDown: 'down', a: 'a', A: 'a', b: 'b', B: 'b', Enter: 'a' };
  if (e.target !== pad && e.key === 'Enter') return;
  const act = map[e.key];
  if (act) { e.preventDefault(); press(act); }
});

// ---------- the one move: pick a world, the whole booklet reprints in its ink
const UI_ICONS = () => $$('.ui-icon[data-icon]');
function applyInk(s) {
  const r = document.documentElement.style;
  r.setProperty('--ink', s.ink); r.setProperty('--on-ink', s.onInk);
  r.setProperty('--ink-hl', s.onInk === '#ffffff' ? '#ff9b8f' : s.ink);
  document.querySelector('meta[name="theme-color"]').setAttribute('content', s.ink);
}
let wipeTimer = null;
function setWorld(slug, { animate = true } = {}) {
  if (!BY[slug]) return;
  const changed = slug !== state.world;
  state.world = slug; store.set('world', slug);
  const s = BY[slug];
  const root = document.documentElement;
  if (animate && changed && !reduced.matches) {
    clearTimeout(wipeTimer);
    root.style.setProperty('--ink-next', s.ink);
    root.classList.remove('reink'); void root.offsetWidth; root.classList.add('reink');
    wipeTimer = setTimeout(() => { applyInk(s); root.classList.remove('reink'); }, 600);
  } else applyInk(s);
  UI_ICONS().forEach((el) => paint(el, slug, el.dataset.icon));
  $$('.item').forEach((b) => paint($('.ic', b), slug, b.dataset.item));
  $$('.level').forEach((row) => { const on = row.dataset.slug === slug; row.classList.toggle('on', on); $('input', row).checked = on; });
  renderStart(); renderPad(); renderCard();
  if (changed) announce(`World ${s.world}-${s.level}: ${s.title}. The manual is now printed in it.`);
}
function setItem(n) { state.item = n; store.set('item', n); renderStart(); renderPad(); renderCard(); }

// ---------- page tabs follow the reader
const tabs = $$('.tabs a');
const io = new IntersectionObserver((entries) => {
  entries.forEach((en) => {
    if (en.isIntersecting) tabs.forEach((a) => a.setAttribute('aria-current', String(a.getAttribute('href') === '#' + en.target.id)));
  });
}, { rootMargin: '-45% 0px -50% 0px' });
['cover', 'start', 'controls', 'worlds', 'items', 'warning'].forEach((id) => io.observe(document.getElementById(id)));

// ---------- start
$('[data-version]').textContent = 'v' + data.version;
buildWorlds();
buildItems();
setWorld(state.world, { animate: false });
showCover();
startCover();
