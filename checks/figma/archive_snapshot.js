// 아카이브 snapshot (읽기 전용). 오케스트레이터가 use_figma로 돌리고, 돌려받은 JSON을
// runs/<폴더>/s6/snapshot-{before|after|final}.json 에 그대로 저장한다.
// 돌리기 전에 아래 ARGS 한 줄만 state.json 값으로 바꾼다. 나머지 줄은 고치지 않는다.
// MCP 응답은 20KB에서 잘린다. 결과 JSON 문자열을 16000자씩 돌려주니, offset을 0 → next로 바꿔 가며 done이 true일 때까지 부르고 chunk를 이어 붙여 저장한다.
const ARGS = {"taken": "before", "handoff": "13861:13437", "en_page": "15:3", "protected": [], "archive_section": null, "offset": 0};

const SCREEN_W = 393, SCREEN_MIN_H = 600;
const isScreen = n => Math.round(n.width) === SCREEN_W && n.height >= SCREEN_MIN_H;
const r = v => Math.round(v);
const fillOf = n => {
  if (!('fills' in n) || !Array.isArray(n.fills) || !n.fills.length || n.fills[0].type !== 'SOLID') return null;
  const f = n.fills[0], c = f.color;
  return `${r(c.r*255)},${r(c.g*255)},${r(c.b*255)}@${(f.opacity ?? 1).toFixed(2)}`;
};
// 구조 해시: 자기 위치(x,y)는 빼고, 자식은 상대 위치까지 넣는다
function sig(n, depth, isRoot) {
  let s = `${n.type}|${n.name}|${r(n.width)}x${r(n.height)}|${n.visible === false ? 'h' : 'v'}|${fillOf(n) || ''}`;
  if (!isRoot) s += `|${r(n.x)},${r(n.y)}`;
  if (n.type === 'TEXT') s += `|${n.characters}`;
  if ('children' in n && depth < 12) s += '[' + n.children.map(c => sig(c, depth + 1, false)).join(';') + ']';
  return s;
}
// 보호 목록용 구조 서명: 안쪽 인스턴스는 속을 펼치지 않고 「이름 · 오버라이드 수 · 위치 · 보임」만 담는다.
// 메인 컴포넌트를 고쳐서 인스턴스 속이 바뀌는 것은 통과시키고, 그 섹션에 직접 손댄 것(노드 추가·삭제·이동·문구·오버라이드)은 잡는다
function psig(n, depth, isRoot) {
  if (n.type === 'INSTANCE' && !isRoot) return `I|${n.name}|ov${n.overrides.length}|${r(n.x)},${r(n.y)}|${n.visible === false ? 'h' : 'v'}`;
  let s = `${n.type}|${n.name}|${r(n.width)}x${r(n.height)}|${n.visible === false ? 'h' : 'v'}|${fillOf(n) || ''}`;
  if (!isRoot) s += `|${r(n.x)},${r(n.y)}`;
  if (n.type === 'TEXT') s += `|${n.characters}`;
  if ('children' in n && depth < 12) s += '[' + n.children.map(c => psig(c, depth + 1, false)).join(';') + ']';
  return s;
}
function hash(str) { let h = 5381; for (let i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) | 0; return (h >>> 0).toString(16); }
const hashOf = n => hash(sig(n, 0, true));
function shallow(n, depth, max) {
  if (depth > max || !('children' in n)) return [];
  return n.children.flatMap(c => [`${c.id}|${c.type}|${c.name}|${r(c.width)}x${r(c.height)}`, ...shallow(c, depth + 1, max)]);
}
function names(n, depth = 0) {
  if (depth > 4) return [];
  const own = `${n.type}:${n.name}${n.type === 'TEXT' ? '«' + n.characters.slice(0, 40) + '»' : ''}`;
  const kids = ('children' in n) ? n.children.flatMap(c => names(c, depth + 1)) : [];
  return [own, ...kids];
}
function screensIn(sec) {
  const out = [];
  (function walk(n) {
    for (const c of n.children) {
      if (c.type === 'SECTION') walk(c);
      else if (isScreen(c)) out.push(c);
    }
  })(sec);
  return out;
}
async function pageOf(n) { let p = n; while (p && p.type !== 'PAGE') p = p.parent; return p; }

const out = { taken: ARGS.taken, args: Object.fromEntries(Object.entries(ARGS).filter(([k]) => k !== 'offset')),  // offset은 빼야 조각마다 같은 JSON이 나온다
  handoff: {}, en_mains: [], pairs: [], lib_frames: [], protected: [], work_page_mains: [], archive: null };

// 1. 핸드오프 섹션
const ho = await figma.getNodeByIdAsync(ARGS.handoff);
if (ho) {
  const hoScreens = screensIn(ho);
  out.handoff = { id: ho.id, name: ho.name, screens: [] };
  for (const s of hoScreens) {
    const row = { id: s.id, name: s.name, type: s.type };
    if (s.type === 'INSTANCE') {
      const m = await s.getMainComponentAsync();
      const p = m ? await pageOf(m) : null;
      row.main_page = p ? p.id : null;
      row.overrides = s.overrides.length;
    }
    if (s.type === 'COMPONENT') out.work_page_mains.push({ id: s.id, name: s.name });
    out.handoff.screens.push(row);
  }
}

// 2. EN 페이지 화면 메인
const en = await figma.getNodeByIdAsync(ARGS.en_page);
await en.loadAsync();
const enMains = en.findAllWithCriteria({ types: ['COMPONENT'] }).filter(isScreen);
const enByName = new Map();
for (const m of enMains) {
  const inst = await m.getInstancesAsync();
  // 인스턴스 오버라이드는 합계만 남긴다 (응답 20KB 한도). 합계가 줄면 어느 화면이 원본으로 돌아갔다는 뜻이다
  out.en_mains.push({ id: m.id, name: m.name, hash: hashOf(m), ov: inst.reduce((t, i) => t + i.overrides.length, 0), n: inst.length });
  enByName.set(m.name, m);
}

// 2-1. 라이브러리 띠 부품(폭 300 이상): EN 메인이 쓰는 것만. 핸드오프에서 같은 이름으로 detach됐고 구조가 다르면 후보
const struct = (n, d = 0) => (d > 4) ? [] : [`${n.type}:${n.name}`, ...(('children' in n) ? n.children.flatMap(c => struct(c, d + 1)) : [])];
const libBars = new Map();
for (const m of enMains) {
  for (const i of m.findAllWithCriteria({ types: ['INSTANCE'] })) {
    if (i.width < 300) continue;
    const mc = await i.getMainComponentAsync();
    if (!mc || !mc.remote) continue;
    const key = (mc.parent && mc.parent.type === 'COMPONENT_SET') ? mc.parent.name : mc.name;
    if (!libBars.has(key)) libBars.set(key, mc);
  }
}
if (ho) {
  for (const s of screensIn(ho)) {
    for (const f of s.findAllWithCriteria({ types: ['FRAME'] })) {
      const mc = libBars.get(f.name);
      if (!mc) continue;
      const a = struct(f).slice(1), b = struct(mc).slice(1);
      const cnt = new Map();
      a.forEach(x => cnt.set(x, (cnt.get(x) || 0) + 1));
      b.forEach(x => cnt.set(x, (cnt.get(x) || 0) - 1));
      const diff = [...cnt.values()].reduce((t, v) => t + Math.abs(v), 0);
      if (diff > 0) out.lib_frames.push({ id: f.id, name: f.name, screen: s.name, diff });
    }
  }
}

{
  const g = new Map();
  for (const f of out.lib_frames) { const x = g.get(f.name) || { id: f.id, name: f.name, screens: 0, diff: 0 }; x.screens++; x.diff = Math.max(x.diff, f.diff); g.set(f.name, x); }
  out.lib_frames = [...g.values()];  // 부품 이름별 한 줄 (처음 본 노드 id · 걸린 화면 수 · 최대 차이)
}

// 3. 같은 이름 짝: 핸드오프의 detach 화면 ↔ EN 메인, 바뀐 노드 수
if (ho) {
  for (const s of screensIn(ho)) {
    const base = s.name.split(' · ')[0].trim();
    const m = enByName.get(base);
    if (!m || s.type === 'INSTANCE' || s.type === 'COMPONENT') continue;
    const a = names(s).slice(1), b = names(m).slice(1);
    const cnt = new Map();
    a.forEach(x => cnt.set(x, (cnt.get(x) || 0) + 1));
    b.forEach(x => cnt.set(x, (cnt.get(x) || 0) - 1));
    const diff = [...cnt.values()].reduce((t, v) => t + Math.abs(v), 0);
    out.pairs.push({ frame_id: s.id, main_id: m.id, name: base, diff });
  }
}

// 4. 보호 목록
for (const id of ARGS.protected) {
  const n = await figma.getNodeByIdAsync(id);
  if (!n) { out.protected.push({ id, missing: true }); continue; }
  if (n.type === 'PAGE') { await n.loadAsync(); out.protected.push({ id, name: n.name, hash: hash(shallow(n, 0, 2).join('\n')) }); }
  else out.protected.push({ id, name: n.name, hash: hash(psig(n, 0, true)) });
}

// 5. 아카이브 섹션 배치 (S6-3 뒤). 응답 20KB 한도 때문에 상자는 배열 [종류, 이름 24자, x, y, w, h, 채움]으로 줄인다
if (ARGS.archive_section) {
  const a = await figma.getNodeByIdAsync(ARGS.archive_section);
  if (a) {
    const T = { FRAME: 'F', INSTANCE: 'I', COMPONENT: 'C', SECTION: 'S', TEXT: 'T', VECTOR: 'V', GROUP: 'G' };
    const box = n => [T[n.type] || '?', n.name.slice(0, 24), r(n.x), r(n.y), r(n.width), r(n.height), fillOf(n)];
    const kids = a.children.map(c => (c.type === 'SECTION') ? [...box(c), c.children.map(box)] : box(c));
    const asIs = a.findAll(n => /\bas-?is\b|\bbefore\b/i.test(n.name)).map(n => n.name);
    const copies = a.findAllWithCriteria({ types: ['FRAME'] }).filter(n => isScreen(n) && enByName.has(n.name)).map(n => n.name);
    const screens = [];
    (function walk(n) { for (const c of n.children) { if (c.type === 'SECTION') walk(c); else if (isScreen(c) && c.name !== '코멘트') screens.push([c.id, c.name]); } })(a);
    out.archive = { box: box(a), children: kids, as_is: asIs, detached_copies: copies, screens };
  }
}
const json = JSON.stringify(out);
const CHUNK = 16000, off = ARGS.offset || 0;
return { total: json.length, offset: off, next: off + CHUNK, done: off + CHUNK >= json.length, chunk: json.slice(off, off + CHUNK) };
