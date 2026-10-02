#!/usr/bin/env python3
"""게이트 판정 스크립트.

사용: python3 checks/gates.py G5 runs/<PRD>
출력: JSON 한 덩어리. 종료 코드 0=통과, 1=실패, 2=셀 수 없음.

판정 기준은 rules.md, 허용 값은 default-wireframe.md 3절 표에서 읽는다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WF = ROOT / "default-wireframe.md"

PASS, FAIL, UNCOUNTABLE = "pass", "fail", "uncountable"


# ── 허용 값 읽기 ─────────────────────────────────────────────

def _table_rows(md_text, section_title):
    """'## 3. …' 절 안의 표를 {항목: 값 칸} 으로 돌려준다."""
    rows = {}
    in_sec = False
    for line in md_text.splitlines():
        if line.startswith("## "):
            in_sec = section_title in line
            continue
        if in_sec and line.startswith("|") and not set(line) <= set("|- "):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] not in ("항목",):
                rows[cells[0]] = cells[1]
    return rows


def _nums_before_period(cell):
    head = cell.split(".")[0]
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", head)}


def _parse_color(s):
    """'#rrggbb' '#rrggbbaa' 'rgb()' 'rgba()' → (r,g,b,a)."""
    s = s.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{6})([0-9a-f]{2})?", s)
    if m:
        h = m.group(1)
        a = int(m.group(2), 16) / 255 if m.group(2) else 1.0
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), round(a, 2))
    m = re.fullmatch(r"rgba?\(([^)]*)\)", s)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",") if p.strip()]
        r, g, b = (int(float(x)) for x in parts[:3])
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return (r, g, b, round(a, 2))
    return None


def load_allowed():
    rows = _table_rows(DEFAULT_WF.read_text(), "목업 안에서 쓸 수 있는 값")
    colors = set()
    for key, cell in rows.items():
        if key.startswith("색"):
            for tok in re.findall(r"`([^`]+)`", cell):
                c = _parse_color(tok)
                if c:
                    colors.add(c)
    return {
        "colors": colors,
        "font_sizes": _nums_before_period(rows.get("글자 크기", "")),
        "weights": _nums_before_period(rows.get("굵기", "")),
        "spacing": _nums_before_period(rows.get("간격", "")) | {0.0},
        "radius": _nums_before_period(rows.get("라운드", "")) | {0.0},
        "icons": _nums_before_period(rows.get("아이콘·이모지", "")),
        "fonts": [f for f in ("NanumSquareRound", "Pretendard") if f in rows.get("글꼴", "")],
    }


def color_allowed(c, allowed):
    return any(c[:3] == a[:3] and abs(c[3] - a[3]) <= 0.01 for a in allowed)


def fmt_color(c):
    r, g, b, a = c
    return f"#{r:02x}{g:02x}{b:02x}" + ("" if a == 1 else f"{round(a * 255):02x}")


# ── 렌더링 ───────────────────────────────────────────────────

COLLECT_JS = r"""
() => {
  const out = [];
  const directText = el => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const label = el => {
    const t = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 24);
    return el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '') + (t ? ` "${t}"` : '');
  };
  for (const scr of document.querySelectorAll('[data-screen]')) {
    const sr = scr.getBoundingClientRect();
    const screen = {name: scr.dataset.screen, w: sr.width, h: sr.height, after: scr.dataset.after || null, els: []};
    for (const el of [scr, ...scr.querySelectorAll('*')]) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect();
      screen.els.push({
        where: label(el),
        isNew: !!el.closest('[data-new]'),
        isOS: !!el.closest('[data-part]'),
        isRoot: el === scr,
        isLib: !!el.closest('[data-lib]'),
        lib: el.dataset.lib || null,
        emoji: directText(el) && /^[\p{Extended_Pictographic}\uFE0F\u200D\s]+$/u.test([...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('')),
        part: el.dataset.part || null,
        text: directText(el),
        color: cs.color, bg: cs.backgroundColor,
        borders: ['Top','Right','Bottom','Left'].map(s => [cs['border'+s+'Width'], cs['border'+s+'Color']]),
        fontSize: cs.fontSize, fontWeight: cs.fontWeight, fontFamily: cs.fontFamily,
        radius: [cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius],
        padding: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft],
        gap: [cs.rowGap, cs.columnGap],
        w: r.width, h: r.height,
      });
    }
    out.push(screen);
  }
  return out;
}
"""


def render(html_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1400, "height": 1000})
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(300)
        screens = pg.evaluate(COLLECT_JS)
        attrs = pg.evaluate(r"""() => ({
          newEls: [...document.querySelectorAll('[data-new]')].map(e => e.dataset.new),
          decisions: [...document.querySelectorAll('[data-decision]')].map(e => ({name: e.dataset.decision, text: e.innerText.trim()})),
          rechecks: [...document.querySelectorAll('[data-recheck]')].map(e => e.innerText.trim()),
          newScreens: [...document.querySelectorAll('[data-new-screen]')].map(s => ({name: s.dataset.newScreen, variants: new Set([...s.querySelectorAll('[data-variant]')].map(v => v.dataset.variant)).size})),
          flows: [...document.querySelectorAll('[data-flow="diary"]')].map(f => ({name: f.dataset.name || f.dataset.screen || '(이름 없음)', inputs: f.querySelectorAll('[data-input="photo"],[data-input="text"]').length + (['photo','text'].includes(f.dataset.input) ? 1 : 0)})),
          afterCapture: [...document.querySelectorAll('[data-screen][data-after="capture"]')].map(s => ({name: s.dataset.screen, dismiss: s.querySelectorAll('[data-action="dismiss"]').length})),
          autostart: document.querySelectorAll('[data-autostart="learning"]').length,
          screenNames: [...document.querySelectorAll('[data-screen]')].map(s => s.dataset.screen),
          text: document.body.innerText,
        })""")
        b.close()
    return screens, attrs


def px(v):
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)px", v.strip())
    return float(m.group(1)) if m else None


def result(gate, status, items=None, human=None, note=None):
    out = {"gate": gate, "result": status, "count": len(items or []), "items": items or []}
    if human:
        out["human"] = human
    if note:
        out["note"] = note
    return out


def wireframe(run):
    p = run / "s3" / "s3-wireframe.html"
    return p if p.exists() else None


def state(run):
    p = run / "state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def md_table(path, required_cols):
    """마크다운 표에서 required_cols 가 모두 있는 첫 표를 [{열: 값}] 으로."""
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        head = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(any(rc in h for h in head) for rc in required_cols):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append(dict(zip(head, cells + [""] * (len(head) - len(cells)))))
            return head, rows
    return None, []


def col(row, key):
    for k, v in row.items():
        if key in k:
            return v
    return ""


# ── 게이트 ───────────────────────────────────────────────────

def g4(run):
    refs = run / "s3" / "s3-refs.md"
    wf = wireframe(run)
    if not refs.exists() or not wf:
        return result("G4", UNCOUNTABLE, note="s3-refs.md 또는 s3-wireframe.html이 없다")
    head, rows = md_table(refs, ["화면", "출처", "무드/용도", "빌릴 것"])
    if head is None:
        return result("G4", UNCOUNTABLE, note="s3-refs.md에 「화면 | 출처 | 무드/용도 | 여기서 빌릴 것」 표가 없다")
    _, attrs = render(wf)
    items = []
    for n, r in enumerate(rows, 1):
        if col(r, "무드/용도") not in ("무드", "용도"):
            items.append({"what": "무드/용도 칸이 「무드」나 「용도」가 아니다", "where": f"{n}행", "value": col(r, "무드/용도")})
        if not col(r, "빌릴 것"):
            items.append({"what": "「여기서 빌릴 것」 칸이 비었다", "where": f"{n}행"})
    covered = {col(r, "화면") for r in rows}
    for s in dict.fromkeys(attrs["screenNames"]):
        if s not in covered:
            items.append({"what": "레퍼런스가 0개인 화면", "where": s})
    return result("G4", FAIL if items else PASS, items)


def _value_violations(screens, allowed):
    items = []
    for scr in screens:
        if abs(scr["w"] - 393) > 0.5:
            items.append({"screen": scr["name"], "what": "목업 폭이 393이 아니다", "value": round(scr["w"], 1)})
        for part, hgt in (("statusbar", 54), ("home-indicator", 34)):
            found = [e for e in scr["els"] if e["part"] == part]
            if len(found) != 1:
                items.append({"screen": scr["name"], "what": f"data-part=\"{part}\"가 {len(found)}개다 (1개여야 한다)"})
            elif abs(found[0]["h"] - hgt) > 0.5 and not (part == "home-indicator" and abs(found[0]["w"] - 139) <= 0.5 and abs(found[0]["h"] - 5) <= 0.5):
                items.append({"screen": scr["name"], "what": f"{part} 높이가 {hgt}가 아니다", "value": round(found[0]["h"], 1)})
        for e in scr["els"]:
            if e["isNew"] or e["isOS"]:
                continue
            def bad(what, value):
                items.append({"screen": scr["name"], "what": what, "value": value, "where": e["where"]})
            if e["text"]:
                c = _parse_color(e["color"])
                if c and c[3] > 0 and not color_allowed(c, allowed["colors"]):
                    bad("글자 색이 표 밖", fmt_color(c))
                fs = px(e["fontSize"])
                if e["emoji"]:
                    if fs is not None and fs not in allowed["icons"]:
                        bad("이모지 크기가 아이콘 표 밖", fs)
                elif fs is not None and fs not in allowed["font_sizes"]:
                    bad("글자 크기가 표 밖", fs)
                if float(e["fontWeight"]) not in allowed["weights"]:
                    bad("굵기가 표 밖", e["fontWeight"])
                first = e["fontFamily"].split(",")[0].strip().strip("'\"")
                if allowed["fonts"] and first not in allowed["fonts"]:
                    bad("글꼴이 표 밖", first)
            c = _parse_color(e["bg"])
            if c and c[3] > 0 and not color_allowed(c, allowed["colors"]):
                bad("배경 색이 표 밖", fmt_color(c))
            for wv, cv in e["borders"]:
                if (px(wv) or 0) > 0:
                    c = _parse_color(cv)
                    if c and c[3] > 0 and not color_allowed(c, allowed["colors"]):
                        bad("테두리 색이 표 밖", fmt_color(c))
            for rv in ([] if e["isRoot"] else e["radius"]):
                if rv.endswith("%"):
                    if rv != "50%":
                        bad("라운드가 표 밖", rv)
                    continue
                v = px(rv.split()[0])
                if v is not None and v not in allowed["radius"]:
                    bad("라운드가 표 밖" + (" (문서용 값)" if v in (14, 18, 42) else ""), v)
            for pv in e["padding"] + [g for g in e["gap"] if g != "normal"]:
                v = px(pv)
                if v is not None and v not in allowed["spacing"]:
                    bad("간격이 표 밖", v)
    # 같은 값이 여러 요소에서 반복되면 한 줄로 묶는다
    seen, dedup = {}, []
    for it in items:
        k = (it["screen"], it["what"], str(it.get("value")))
        if k in seen:
            seen[k]["n"] = seen[k].get("n", 1) + 1
        else:
            seen[k] = it
            dedup.append(it)
    return dedup


def g5(run):
    wf = wireframe(run)
    if not wf:
        return result("G5", UNCOUNTABLE, note="s3-wireframe.html이 없다")
    screens, _ = render(wf)
    if not screens:
        return result("G5", UNCOUNTABLE, note="data-screen 표시가 0개라 셀 수 없다")
    items = _value_violations(screens, load_allowed())
    return result("G5", FAIL if items else PASS, items)


def g6(run):
    wf = wireframe(run)
    if not wf:
        return result("G6", UNCOUNTABLE, note="s3-wireframe.html이 없다")
    _, attrs = render(wf)
    names = list(dict.fromkeys(attrs["newEls"]))
    if not names:
        return result("G6", PASS, note="신규 표시(data-new) 0개")
    listfile = run / "s3" / "s3-new.md"
    if not listfile.exists():
        return result("G6", FAIL, [{"what": "신규 표시가 있는데 s3-new.md가 없다", "value": names}])
    _, rows = md_table(listfile, ["이름", "이유"])
    listed = {col(r, "이름"): col(r, "이유") for r in rows}
    items = []
    for n in names:
        if n not in listed:
            items.append({"what": "신규 컴포넌트 목록에 없다", "where": n})
        elif not listed[n]:
            items.append({"what": "이유 칸이 비었다", "where": n})
    return result("G6", FAIL if items else PASS, items)


HUMAN_7 = ["자리 고정", "사진 위 흰 글자 스크림", "빈자리는 초대로", "강한 부품 전부/전무",
           "층(카드 안 카드·1px 헤어라인)", "교정 표시 색", "오버슈트 곡선", "보라·파랑 그라데이션"]


def g7(run):
    wf = wireframe(run)
    if not wf:
        return result("G7", UNCOUNTABLE, note="s3-wireframe.html이 없다")
    screens, attrs = render(wf)
    if not screens:
        return result("G7", UNCOUNTABLE, note="data-screen 표시가 0개라 셀 수 없다")
    green = (19, 80, 0, 1.0)
    items = []
    for scr in screens:
        area = scr["w"] * scr["h"] or 1
        faces = [e for e in scr["els"] if _parse_color(e["bg"]) == green and e["w"] * e["h"] >= 2000]
        g_area = sum(e["w"] * e["h"] for e in faces)
        if len(faces) > 1:
            items.append({"screen": scr["name"], "what": "숲 그린 면이 2개 이상", "value": len(faces), "where": [e["where"] for e in faces]})
        if g_area / area > 0.10:
            items.append({"screen": scr["name"], "what": "숲 그린 면적이 10% 초과", "value": f"{g_area / area:.0%}"})
        for e in scr["els"]:
            if e["lib"] == "ButtonFull":
                c = _parse_color(e["bg"])
                if not c or c[3] == 0:
                    items.append({"screen": scr["name"], "what": "ButtonFull 배경이 투명하다 (그려지지 않은 면은 초록 면 규칙을 피해 간다)", "where": e["where"]})
        big = [e for e in scr["els"] if e["text"] and not e["isLib"] and not e["emoji"] and px(e["fontSize"]) in (28.0, 22.0)]  # 이모지는 글자가 아니라 그림 (G5와 같은 기준, 26-10-02)
        if len(big) > 1:
            items.append({"screen": scr["name"], "what": "28·22 글자가 2개 이상", "value": len(big), "where": [e["where"] for e in big]})
    for d in attrs["decisions"]:
        if "근거:" not in d["text"] and "근거 못 찾음" not in d["text"]:
            items.append({"what": "형태 결정에 「근거:」나 「근거 못 찾음」이 없다", "where": d["name"]})
    filled = [t for t in attrs["rechecks"] if t]
    if len(filled) != 1:
        items.append({"what": "되묻기 답(data-recheck)이 1개가 아니다", "value": len(filled)})
    for s in attrs["newScreens"]:
        if not 5 <= s["variants"] <= 7:
            items.append({"what": "새 화면 구조안이 5~7개가 아니다", "where": s["name"], "value": s["variants"]})
    return result("G7", FAIL if items else PASS, items, human=HUMAN_7)


SKIP_HEAD = re.compile(r"out of scope|안 하는 것|고려한 대안|기각|리스크", re.I)
NEGATION = re.compile(r"안 함|하지 않|않는다|않고|제외|기각|금지|없다|대신 .*본인")
AI_DAY = [re.compile(p) for p in (
    r"하루(를|의)?\s*(한 문장으로\s*)?(요약|정리)",
    r"(AI|에이아이)가\s*(일기|하루)(를)?\s*(대신|자동으로)",
)]


def g13(run):
    wf = wireframe(run)
    st = state(run)
    items, notes = [], []
    # 1) AI가 사용자 대신 하루를 정리하는 기능 0개
    sources = [run / "s2" / "s2-prd.md", run / "s5" / "s5-policy-cards.md"]
    texts = [(p.name, p.read_text()) for p in sources if p.exists()]
    attrs = None
    if wf:
        _, attrs = render(wf)
        texts.append((wf.name, attrs["text"]))
    for name, text in texts:
        skip = False
        for ln, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                skip = bool(SKIP_HEAD.search(line))
                continue
            if skip or NEGATION.search(line):
                continue
            for pat in AI_DAY:
                if pat.search(line):
                    items.append({"what": "AI가 사용자 대신 하루를 정리하는 기능", "where": f"{name}:{ln}", "value": line.strip()[:60]})
    if not wf:
        notes.append("s3-wireframe.html이 없어 흐름 검사를 건너뛰었다")
        return result("G13", FAIL if items else UNCOUNTABLE, items, note="; ".join(notes))
    # 2) 일기 흐름마다 사용자 입력 1개 이상
    if st.get("record_feature") and not attrs["flows"]:
        return result("G13", UNCOUNTABLE, items, note="기록 기능 PRD인데 data-flow=\"diary\" 표시가 0개라 셀 수 없다")
    for f in attrs["flows"]:
        if f["inputs"] < 1:
            items.append({"what": "사용자 입력 없이 일기를 만드는 흐름", "where": f["name"]})
    # 3) 기록 기능 PRD면: 찍은 직후 화면에 닫기, 자동 학습 시작 0
    if st.get("record_feature"):
        if not attrs["afterCapture"]:
            return result("G13", UNCOUNTABLE, items, note="기록 기능 PRD인데 data-after=\"capture\" 화면이 0개라 셀 수 없다")
        for s in attrs["afterCapture"]:
            if s["dismiss"] < 1:
                items.append({"what": "사진을 찍은 직후 화면에 닫기가 없다", "where": s["name"]})
        if attrs["autostart"]:
            items.append({"what": "학습이 저절로 시작되는 흐름", "value": attrs["autostart"]})
    return result("G13", FAIL if items else PASS, items)


# ── S2 · S4 · S5 게이트 (문서 형식으로 센다) ──────────────────

def _section_lines(text, title_pat):
    """제목이 title_pat에 맞는 절의 본문 줄들."""
    out, on = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            on = bool(re.search(title_pat, line))
            continue
        if on:
            out.append(line)
    return out


METRIC = re.compile(r"\d[\d,.]*\s*(%|명|건|회|배)")


def g1(run):
    prd, ana = run / "s2" / "s2-prd.md", run / "s2" / "s2-analysis.md"
    if not prd.exists() or not ana.exists():
        return result("G1", UNCOUNTABLE, note="s2-prd.md 또는 s2-analysis.md가 없다")
    head, rows = md_table(ana, ["번호", "이벤트", "분모", "기간", "결과"])
    if head is None:
        return result("G1", UNCOUNTABLE, note="s2-analysis.md에 「번호 | 이벤트 | 분모 | 기간 | 결과」 표가 없다")
    items = []
    known = set()
    for r in rows:
        q = col(r, "번호")
        known.add(q)
        for k in ("이벤트", "분모", "기간", "결과"):
            if not col(r, k):
                items.append({"what": f"쿼리 {k} 칸이 비었다", "where": q})
        if any("재실행" in h for h in head) and col(r, "재실행") != col(r, "결과"):
            items.append({"what": "다시 돌린 값이 결과와 다르다", "where": q, "value": f"{col(r, '결과')} → {col(r, '재실행')}"})
    skip = False
    for ln, line in enumerate(prd.read_text().splitlines(), 1):
        if line.lstrip().startswith("#"):
            skip = "문서점검" in line
            continue
        if skip or not METRIC.search(line):
            continue
        tags = re.findall(r"\[(Q\d+)\]", line)
        if not tags:
            items.append({"what": "쿼리 번호가 없는 숫자", "where": f"s2-prd.md:{ln}", "value": line.strip()[:60]})
        for t in tags:
            if t not in known:
                items.append({"what": "s2-analysis.md에 없는 쿼리 번호", "where": f"s2-prd.md:{ln}", "value": t})
    return result("G1", FAIL if items else PASS, items,
                  human=[] if any("재실행" in h for h in head) else ["s2-analysis.md에 「재실행」 열이 없어 다시 돌린 값은 못 셌다"])


def g2(run):
    import subprocess
    prd = run / "s2" / "s2-prd.md"
    if not prd.exists():
        return result("G2", UNCOUNTABLE, note="s2-prd.md가 없다")
    lint = Path.home() / ".claude" / "scripts" / "writing-lint.py"
    out = subprocess.run([sys.executable, str(lint), str(prd)], capture_output=True, text=True).stdout
    items = []
    if "기계로 잡히는 항목 0건" not in out:
        m = re.search(r"— (\d+)건", out)
        items.append({"what": "writing-lint 확정 위반", "value": int(m.group(1)) if m else "?"})
    answers = [l for l in _section_lines(prd.read_text(), "문서점검") if re.match(r"\s*(\d+[.)]|[-*])\s+\S", l)]
    if len(answers) != 9:
        items.append({"what": "「문서점검 9개」 절의 답이 9줄이 아니다", "value": len(answers)})
    return result("G2", FAIL if items else PASS, items)


LOG_KEYS = ["지적 원문", "내 원래 논리", "뛴 지점", "유형", "다음에 걸 질문"]


def g3(run):
    d = run / "s2"
    lr, rc, lg = d / "logic-review.md", d / "review-comments.md", d / "log-draft.md"
    items = []
    if not lr.exists() or not lr.read_text().strip():
        items.append({"what": "리뷰 전 logic-review 결과(s2/logic-review.md)가 없다"})
    if not rc.exists():
        return result("G3", UNCOUNTABLE, items, note="review-comments.md가 없다. 사수 리뷰 전이면 G3은 리뷰 뒤에 센다")
    n_comments = len([l for l in rc.read_text().splitlines() if re.match(r"\s*\d+[.)]\s+\S", l)])
    blocks = re.split(r"(?m)^### ", lg.read_text())[1:] if lg.exists() else []
    if n_comments != len(blocks):
        items.append({"what": "리뷰 지적 수와 로그 항목 수가 다르다", "value": f"지적 {n_comments} / 로그 {len(blocks)}"})
    for b in blocks:
        title = b.splitlines()[0].strip()
        for k in LOG_KEYS:
            m = re.search(rf"\|\s*{k}\s*\|\s*(.*?)\s*\|", b)
            if not m or not m.group(1):
                items.append({"what": f"「{k}」 칸이 비었다", "where": title})
    return result("G3", FAIL if items else PASS, items)


def _lint_line(path, label):
    """에이전트가 적어 둔 'label: N' 줄에서 N을 읽는다."""
    if not path.exists():
        return None
    m = re.search(rf"{label}\s*:\s*(\d+)", path.read_text())
    return int(m.group(1)) if m else None


def g8(run):
    p = run / "s4" / "s4-figma.md"
    n = _lint_line(p, "figma-lint 결과")
    if n is None:
        return result("G8", UNCOUNTABLE, note="s4-figma.md에 「figma-lint 결과: N」 줄이 없다")
    items = [{"what": "figma-lint 결과가 0이 아니다", "value": n}] if n else []
    m = _lint_line(p, "신규 표시 없는 새 부품")
    if m:
        items.append({"what": "「신규」 표시 없는 새 부품", "value": m})
    return result("G8", FAIL if items else PASS, items)


def g9(run):
    p = run / "s4" / "s4-figma.md"
    if not p.exists():
        return result("G9", UNCOUNTABLE, note="s4-figma.md가 없다")
    head, rows = md_table(p, ["번호", "지적", "반영/보류", "보류 이유", "고친 개수", "미리 잡았나"])
    if head is None:
        return result("G9", UNCOUNTABLE, note="s4-figma.md에 컨펌 코멘트 표가 없다. 컨펌 전이면 G9는 컨펌 뒤에 센다")
    items = []
    for r in rows:
        q = col(r, "번호")
        if col(r, "반영/보류") not in ("반영", "보류"):
            items.append({"what": "반영/보류 칸이 비었거나 다른 값", "where": q})
        if col(r, "반영/보류") == "보류" and not col(r, "보류 이유"):
            items.append({"what": "보류 이유가 비었다", "where": q})
        if not re.fullmatch(r"\d+", col(r, "고친 개수")):
            items.append({"what": "같은 부류 고친 개수가 숫자가 아니다", "where": q})
        if col(r, "미리 잡았나") not in ("예", "아니오"):
            items.append({"what": "「게이트가 미리 잡았나」가 예·아니오가 아니다", "where": q})
    return result("G9", FAIL if items else PASS, items)


def g10(run):
    n = _lint_line(run / "s5" / "s5-handoff.md", "figma-lint 14번")
    if n is None:
        return result("G10", UNCOUNTABLE, note="s5-handoff.md에 「figma-lint 14번: N」 줄이 없다")
    return result("G10", FAIL if n else PASS, [{"what": "정책 카드 문체 위반", "value": n}] if n else [])


CARD_MAX_BLOCKS, CARD_MAX_BULLETS = 4, 14  # 지아 기준 카드(13828:284857) 길이
REASON = re.compile(r"왜냐하면|때문에|때문이|검토|대안|고민|논의|리서치")


def _cards(run):
    """s5-policy-cards.md를 [{title, lines}]로. 카드는 '## 카드: …'로 시작한다."""
    p = run / "s5" / "s5-policy-cards.md"
    if not p.exists():
        return None
    cards, cur = [], None
    for line in p.read_text().splitlines():
        if line.startswith("## 카드:"):
            cur = {"title": line[len("## 카드:"):].strip(), "lines": []}
            cards.append(cur)
        elif line.startswith("#"):
            cur = None  # 카드가 아닌 절(메모 등)은 마지막 카드에 붙이지 않는다
        elif cur is not None and line.strip():
            cur["lines"].append(line)
    return cards or None


def g11(run):
    cards = _cards(run)
    if cards is None:
        return result("G11", UNCOUNTABLE, note="s5-policy-cards.md에 「## 카드: …」 카드가 없다")
    items = []
    for c in cards:
        for l in c["lines"]:
            if l.lstrip().startswith("참조"):
                continue
            if REASON.search(l):
                items.append({"what": "카드에 결정 과정·이유 표현", "where": c["title"], "value": l.strip()[:60]})
        heads = [l for l in c["lines"] if re.match(r"\s*\[.+\]\s*$", l)]
        bullets_n = [l for l in c["lines"] if l.lstrip().startswith("- ")]
        if not heads:
            items.append({"what": "[소제목] 줄이 없다", "where": c["title"]})
        if len(heads) > CARD_MAX_BLOCKS or len(bullets_n) > CARD_MAX_BULLETS:
            items.append({"what": f"카드가 길다 (소제목 {CARD_MAX_BLOCKS}개·글머리표 {CARD_MAX_BULLETS}줄 이하로 나눌 것)", "where": c["title"], "value": f"소제목 {len(heads)} · 글머리표 {len(bullets_n)}"})
    titles = [c["title"] for c in cards]
    for t in set(titles):
        if titles.count(t) > 1:
            items.append({"what": "같은 이름의 카드가 두 번 있다", "where": t})
    bullets = {}
    for c in cards:
        for l in c["lines"]:
            b = l.strip()
            if b.startswith("- ") and len(b) > 8:
                bullets.setdefault(b, []).append(c["title"])
    for b, where in bullets.items():
        if len(where) > 1:
            items.append({"what": "같은 정책 줄이 여러 카드에 반복된다 (기본 정책 카드 한 곳에만)", "where": where, "value": b[:60]})
    return result("G11", FAIL if items else PASS, items)


def g12(run):
    cards = _cards(run)
    if cards is None:
        return result("G12", UNCOUNTABLE, note="s5-policy-cards.md에 「## 카드: …」 카드가 없다")
    items = [{"what": "PRD 참조 링크가 없는 카드", "where": c["title"]}
             for c in cards if not any(l.lstrip().startswith("참조") and re.search(r"https?://|\]\(", l) for l in c["lines"])]
    return result("G12", FAIL if items else PASS, items)


EDGE_CATS = ["권한", "실패", "빈 상태", "한도", "시간", "언어", "로그인", "다크", "진입"]
EDGE_OK = ("화면", "정책", "공통", "지아 결정", "해당 없음")


def g14(run):
    p = run / "s3" / "s3-edge-cases.md"
    if not p.exists():
        return result("G14", UNCOUNTABLE, note="s3-edge-cases.md가 없다")
    head, rows = md_table(p, ["분류", "케이스", "처리"])
    if head is None:
        return result("G14", UNCOUNTABLE, note="s3-edge-cases.md에 「분류 | 케이스 | 처리」 표가 없다")
    items = []
    seen = " ".join(col(r, "분류") for r in rows)
    for cat in EDGE_CATS:
        if cat not in seen:
            items.append({"what": "점검하지 않은 엣지케이스 분류", "where": cat})
    for r in rows:
        h = col(r, "처리")
        if not h.startswith(EDGE_OK):
            items.append({"what": "처리 칸이 화면·정책·공통·지아 결정·해당 없음 중 하나가 아니다", "where": col(r, "케이스"), "value": h})
        if h.startswith("지아 결정") and not col(r, "기본값"):
            items.append({"what": "지아 결정 줄에 기본값 제안이 없다 (물을 때는 기본값과 함께)", "where": col(r, "케이스")})
    return result("G14", FAIL if items else PASS, items)


def g15(run):
    p = run / "s5" / "s5-events.md"
    if not p.exists():
        return result("G15", UNCOUNTABLE, note="s5-events.md가 없다")
    head, rows = md_table(p, ["이벤트", "속성", "화면", "PRD", "바뀐 점"])
    if head is None:
        return result("G15", UNCOUNTABLE, note="s5-events.md에 「이벤트 | 속성·값 | 화면(노드) | PRD 8절에 있나 | 바뀐 점」 표가 없다")
    items = []
    for r in rows:
        ev = col(r, "이벤트")
        if not re.search(r"\d+:\d+", col(r, "화면")):
            items.append({"what": "어노테이션을 단 화면 노드가 없다", "where": ev})
        if col(r, "PRD").startswith("아니") and not col(r, "바뀐 점"):
            items.append({"what": "PRD에 없는 이벤트인데 바뀐 점(제안 이유) 칸이 비었다", "where": ev})
        if not re.fullmatch(r"\(?제안\)?\s*`?[a-z][a-z0-9_]*`?|`?[a-z][a-z0-9_]*`?", ev.strip()):
            items.append({"what": "이벤트 이름이 snake_case가 아니다", "where": ev})
    return result("G15", FAIL if items else PASS, items)


# ── S6 아카이브 (G16~G20) ─────────────────────────────────────
# 숫자는 오케스트레이터가 checks/figma/archive_snapshot.js로 만든 snapshot-*.json에서 센다.
# 배치값은 default-archive.md에서 읽는다.

DEFAULT_AR = ROOT / "default-archive.md"
S6_PROC = ("메인 수정", "컴포넌트로 만들기", "새 컴포넌트", "라이브러리 수정", "해당 없음")
NODE_ID = re.compile(r"\d+:\d+")


def _snap(run, which):
    p = run / "s6" / f"snapshot-{which}.json"
    return json.loads(p.read_text()) if p.exists() else None


def _impact(run):
    p = run / "s6" / "s6-impact.md"
    if not p.exists():
        return None
    head, rows = md_table(p, ["화면", "처리"])
    return rows if head else None


def _keep_groups(run):
    p = run / "s6" / "s6-impact.md"
    if not p.exists():
        return set()
    head, rows = md_table(p, ["남길 묶음"])
    return {re.sub(r"\s*\(\d+:\d+\)\s*$", "", col(r, "남길 묶음")).strip() for r in rows} if head else set()


def _ar_values():
    """default-archive.md 표에서 배치 숫자를 읽는다."""
    text = DEFAULT_AR.read_text()
    rows = {}
    for sec in ("바깥", "안"):
        rows.update(_table_rows(text, sec))
    first = lambda key, pat: int(re.search(pat, rows.get(key, "")).group(1))
    m = re.search(r"바뀐 노드 (\d+)개 이하", text)
    return {
        "title_h": first("제목 바", r"높이 (\d+)"),
        "flow_start": first("흐름 섹션 시작", r"y = (\d+)"),
        "flow_gap": first("흐름 섹션 쌓기", r"사이 간격 (\d+)"),
        "flow_fill": "255,255,255@%.2f" % (first("흐름 섹션 채움", r"(\d+)%") / 100),
        "pad": first("안쪽 여백", r"(\d+)"),
        "label_h": first("묶음 라벨", r"높이 (\d+)"),
        "label_fill": "255,255,255@%.2f" % (first("묶음 라벨", r"흰색 (\d+)%") / 100),
        "label_to_screen": first("라벨 → 화면", r"(\d+)"),
        "screen_gap": first("화면 순서", r"화면 사이 (\d+)"),
        "row_gap": first("줄 사이", r"라벨 (\d+)"),
        "card_gap": first("화면 → 그 화면의 카드", r"(\d+)"),
        "small": int(m.group(1)) if m else 10,
    }


def _hex_fill(hexcode):
    h = hexcode.lstrip("#")
    return "%d,%d,%d@1.00" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def g16(run):
    snap, rows = _snap(run, "before"), _impact(run)
    if snap is None:
        return result("G16", UNCOUNTABLE, note="s6/snapshot-before.json이 없다")
    if rows is None:
        return result("G16", UNCOUNTABLE, note="s6-impact.md에 「화면 | … | 처리」 표가 없다")
    en_page = snap.get("args", {}).get("en_page")
    cands = {}
    for p in snap.get("pairs", []):
        cands[p["name"]] = p["frame_id"]
    for s in snap.get("handoff", {}).get("screens", []):
        if s.get("type") == "INSTANCE" and s.get("main_page") == en_page and s.get("overrides", 0) > 0:
            cands[s["name"]] = s["id"]
    for f in snap.get("lib_frames", []):
        cands.setdefault(f["name"], f["id"])
    items = []
    for key, nid in cands.items():
        if not any(key in col(r, "화면") or nid in col(r, "핸드오프 노드") for r in rows):
            items.append({"what": "영향 후보가 s6-impact.md에 없다", "where": key, "value": nid})
    for r in rows:
        proc = col(r, "처리")
        if not proc.startswith(S6_PROC):
            items.append({"what": "처리 칸이 정해진 5개 밖이다", "where": col(r, "화면"), "value": proc})
        if proc.startswith("새 컴포넌트") and not col(r, "이유"):
            items.append({"what": "「새 컴포넌트」인데 이유 칸이 비었다", "where": col(r, "화면")})
    return result("G16", FAIL if items else PASS, items)


def g17(run):
    before, after, rows = _snap(run, "before"), _snap(run, "after"), _impact(run)
    if after is None or before is None:
        return result("G17", UNCOUNTABLE, note="s6/snapshot-before.json 또는 snapshot-after.json이 없다")
    if rows is None:
        return result("G17", UNCOUNTABLE, note="s6-impact.md 표가 없다")
    comps = {m["id"] for m in after.get("en_mains", [])}
    comps |= {s["id"] for s in after.get("handoff", {}).get("screens", []) if s.get("type") == "COMPONENT"}
    small = _ar_values()["small"]
    pairs = before.get("pairs", [])
    items = []
    for r in rows:
        proc, name = col(r, "처리"), col(r, "화면")
        if proc.startswith(("메인 수정", "컴포넌트로 만들기")):
            ids = NODE_ID.findall(col(r, "기존 메인")) or NODE_ID.findall(col(r, "핸드오프 노드"))
            if not ids:
                items.append({"what": "고칠 메인의 노드 id가 없다", "where": name})
            elif ids[0] not in comps:
                items.append({"what": "메인 수정·컴포넌트로 만들기 대상이 COMPONENT가 아니다", "where": name, "value": ids[0]})
        if proc.startswith("새 컴포넌트"):
            hid = NODE_ID.findall(col(r, "핸드오프 노드"))
            p = next((p for p in pairs if (hid and p["frame_id"] == hid[0]) or p["name"] in name), None)
            if p and p["diff"] <= small:
                items.append({"what": f"바뀐 노드가 {small}개 이하인데 새 컴포넌트로 처리했다 (메인을 고칠 것)", "where": name, "value": p["diff"]})
    return result("G17", FAIL if items else PASS, items)


def g18(run):
    before, after, rows = _snap(run, "before"), _snap(run, "after"), _impact(run)
    if after is None or before is None:
        return result("G18", UNCOUNTABLE, note="s6/snapshot-before.json 또는 snapshot-after.json이 없다")
    if rows is None:
        return result("G18", UNCOUNTABLE, note="s6-impact.md 표가 없다")
    listed = set()
    for r in rows:
        listed |= set(NODE_ID.findall(col(r, "기존 메인"))) | set(NODE_ID.findall(col(r, "핸드오프 노드")))
    listed |= set(state(run).get("touched_mains", []))
    b_mains = {m["id"]: m for m in before.get("en_mains", [])}
    items = []
    for m in after.get("en_mains", []):
        old = b_mains.get(m["id"])
        if not old:
            continue
        if m["hash"] != old["hash"] and m["id"] not in listed:
            items.append({"what": "s6-impact.md에 없는 메인이 바뀌었다 (S6-1로 돌아가 목록에 더할 것)", "where": m["name"], "value": m["id"]})
        if m.get("ov", 0) < old.get("ov", 0):  # snapshot은 메인마다 인스턴스 오버라이드 합계만 담는다
            items.append({"what": "고친 메인의 인스턴스 오버라이드 합계가 줄었다 (다른 화면이 원본으로 돌아갔다)", "where": m["name"], "value": f'{old.get("ov")} → {m.get("ov")}'})
    b_prot = {p["id"]: p for p in before.get("protected", [])}
    if not b_prot:
        items.append({"what": "보호 목록이 비었다 (state.json protected)"})
    for p in after.get("protected", []):
        old = b_prot.get(p["id"])
        if p.get("missing") or (old and p.get("hash") != old.get("hash")):
            items.append({"what": "보호 목록 노드가 바뀌었다", "where": p.get("name", p["id"]), "value": p["id"]})
    return result("G18", FAIL if items else PASS, items)


_TYPES = {"F": "FRAME", "I": "INSTANCE", "C": "COMPONENT", "S": "SECTION", "T": "TEXT", "V": "VECTOR", "G": "GROUP"}


def _expand_archive(a):
    """snapshot의 줄인 상자 배열 [종류, 이름, x, y, w, h, 채움, (자식)]을 dict로 편다. 샘플처럼 이미 dict면 그대로 둔다."""
    if "box" not in a:
        return a
    def box(b):
        d = {"type": _TYPES.get(b[0], b[0]), "name": b[1], "x": b[2], "y": b[3], "w": b[4], "h": b[5], "fill": b[6]}
        if len(b) > 7:
            d["children"] = [box(k) for k in b[7]]
        return d
    out = box(a["box"])
    out["children"] = [box(c) for c in a["children"]]
    out["as_is"] = a.get("as_is", [])
    out["detached_copies"] = a.get("detached_copies", [])
    out["screens"] = [{"id": i, "name": n} for i, n in a.get("screens", [])]
    return out


def g19(run):
    final, before = _snap(run, "final"), _snap(run, "before")
    if final is None or not final.get("archive"):
        return result("G19", UNCOUNTABLE, note="s6/snapshot-final.json에 archive 섹션이 없다 (ARGS.archive_section)")
    v = _ar_values()
    a = _expand_archive(final["archive"])
    items, layout = [], []  # items = 구조(통과·실패를 가름), layout = 배치 간격(참고만. 26-10-02 지아: 배치는 사람이 보고 정한다)
    bad = lambda what, where, value=None: items.append({"what": what, "where": where, **({"value": value} if value is not None else {})})
    note = lambda what, where, value=None: layout.append({"what": what, "where": where, **({"value": value} if value is not None else {})})
    sec_fill = _hex_fill(re.search(r"#([0-9A-Fa-f]{6})", _table_rows(DEFAULT_AR.read_text(), "바깥").get("기능 섹션", "")).group(0))
    if a.get("fill") != sec_fill:
        note("기능 섹션 채움이 다르다", a["name"], a.get("fill"))
    title = next((c for c in a["children"] if c["type"] == "FRAME" and c["x"] == 100 and c["y"] == 100), None)
    if not title or title["h"] != v["title_h"] or title["w"] != a["w"] - 200:
        note("제목 바가 (100,100) · 높이·폭 기준과 다르다", a["name"], title and f'{title["w"]}x{title["h"]}')
    flows = sorted((c for c in a["children"] if c["type"] == "SECTION"), key=lambda c: (c["y"], c["x"]))
    if not flows:
        bad("흐름 섹션이 없다", a["name"])
    rows = []  # 위쪽이 같은 흐름 섹션끼리 한 줄
    for f in flows:
        if rows and rows[-1][0]["y"] == f["y"]:
            rows[-1].append(f)
        else:
            rows.append([f])
    want_y = v["flow_start"]
    for row in rows:
        if row[0]["y"] != want_y:
            note("흐름 섹션 줄 위치가 기준과 다르다 (시작 y·줄 사이 간격)", row[0]["name"], f"{row[0]['y']} (기준 {want_y})")
        want_x = 100
        for f in row:
            if f["x"] != want_x:
                note("흐름 섹션 가로 위치가 기준과 다르다 (x 100·사이 간격)", f["name"], f"{f['x']} (기준 {want_x})")
            want_x = f["x"] + f["w"] + v["flow_gap"]
        want_y = row[0]["y"] + max(f["h"] for f in row) + v["flow_gap"]
    for f in flows:
        if f.get("fill") != v["flow_fill"]:
            note("흐름 섹션 채움이 다르다", f["name"], f.get("fill"))
        kids = f.get("children", [])
        if kids and (min(k["x"] for k in kids) != v["pad"] or min(k["y"] for k in kids) != v["pad"]):
            note("흐름 섹션 안쪽 여백이 기준과 다르다", f["name"])
        labels = [k for k in kids if k["type"] == "FRAME" and k["h"] == v["label_h"]]
        screens = [k for k in kids if k["w"] == 393 and k["h"] >= 600 and k["name"] != "코멘트"]
        for l in labels:
            if l.get("fill") != v["label_fill"]:
                note("묶음 라벨 채움이 다르다", f'{f["name"]} · {l["name"]}', l.get("fill"))
            above = [k for k in kids if k is not l and k["type"] != "VECTOR" and k["y"] + k["h"] <= l["y"]]  # 위 줄 전체(카드 포함)
            if above and l["y"] - max(k["y"] + k["h"] for k in above) != v["row_gap"]:
                note("줄 사이 간격이 기준과 다르다 (위 줄 가장 아래 끝 → 라벨)", f'{f["name"]} · {l["name"]}', l["y"] - max(k["y"] + k["h"] for k in above))
        for s in screens:
            if not any(l["x"] <= s["x"] and l["x"] + l["w"] >= s["x"] + 393 and s["y"] - (l["y"] + l["h"]) == v["label_to_screen"] for l in labels):
                note("화면 위에 기준 간격의 묶음 라벨이 없다", f'{f["name"]} · {s["name"]}')
        # 가로 간격은 화면·넓은 기본 정책 카드·남길 묶음끼리만 잰다. 화면 아래 카드(폭 393)는 따로 잰다
        is_under_card = lambda k: k["name"] == "코멘트" and k["w"] == 393
        row_items = sorted((k for k in kids if k["type"] != "VECTOR" and not is_under_card(k)
                            and (k in screens or k["type"] == "SECTION" or k["name"] == "코멘트")), key=lambda k: (k["y"], k["x"]))
        for x1, x2 in zip(row_items, row_items[1:]):
            if x1["y"] == x2["y"] and x2["x"] - (x1["x"] + x1["w"]) != v["screen_gap"]:
                note("같은 줄 가로 간격이 기준과 다르다", f'{f["name"]} · {x1["name"]} → {x2["name"]}', x2["x"] - (x1["x"] + x1["w"]))
        for c in (k for k in kids if is_under_card(k) and k["y"] > 218):
            above = [k for k in kids if k is not c and k["x"] == c["x"] and k["type"] != "VECTOR" and k["y"] < c["y"]]
            if above and c["y"] - max(k["y"] + k["h"] for k in above) != v["card_gap"]:
                note("화면 아래 카드 간격이 기준과 다르다 (바로 위 화면·카드 → 카드)", f'{f["name"]} · 코멘트 x{c["x"]}', c["y"] - max(k["y"] + k["h"] for k in above))
        keep = _keep_groups(run)
        for k in kids:
            if k["type"] == "SECTION" and k["name"] not in keep:
                bad("묶기만 하는 중첩 섹션이 남았다 (s6-impact.md 「남길 묶음」에 없음)", f'{f["name"]} · {k["name"]}')
    for n in a.get("as_is", []) + [n for n in a.get("all_names", []) if re.search(r"(?i)\bas-?is\b|\bbefore\b", n)]:
        bad("As-is 노드가 남았다", n)
    en_names = {m["name"] for m in final.get("en_mains", [])}
    for n in a.get("detached_copies", []) + [n for n in a.get("screen_frames", []) if n in en_names]:
        bad("기존 화면의 detach 사본이 남았다 (메인 인스턴스로 바꿀 것)", n)
    for m in final.get("work_page_mains", []):
        bad("「작업 요청」 페이지에 화면 메인이 남았다", m["name"], m["id"])
    if before:
        got_ids = {s["id"] for s in a.get("screens", [])}
        got_names = {s["name"] for s in a.get("screens", [])}
        renames = state(run).get("approvals", {}).get("A3", {}).get("names", {})  # A3에서 승인한 새 이름
        for s in before.get("handoff", {}).get("screens", []):
            if s["name"] == "코멘트":
                continue
            if s["id"] not in got_ids and s["name"] not in got_names and renames.get(s["name"]) not in got_names:
                bad("핸드오프 화면이 FullScreen에 없다", s["name"], s["id"])
    return result("G19", FAIL if items else PASS, items, human=layout or None)


def g20(run):
    import subprocess
    log = run / "s6" / "s6-library-log.md"
    after = _snap(run, "final") or _snap(run, "after")
    before = _snap(run, "before")
    if not log.exists():
        return result("G20", UNCOUNTABLE, note="s6-library-log.md가 없다")
    if after is None or before is None:
        return result("G20", UNCOUNTABLE, note="snapshot-before.json과 snapshot-after(final).json이 필요하다")
    text = log.read_text()
    items = []
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines or not re.match(r"^`*\[\d{2}-\d{2}-\d{2}\]", lines[0].strip()):
        items.append({"what": "첫 줄이 「[YY-MM-DD] 변경 주제」 제목이 아니다"})
    b = {m["id"]: m["hash"] for m in before.get("en_mains", [])}
    changed = [m["name"] for m in after.get("en_mains", []) if b.get(m["id"]) != m["hash"]]
    rows = _impact(run) or []
    changed += [col(r, "화면") for r in rows if col(r, "처리").startswith("라이브러리 수정")]
    for n in dict.fromkeys(changed):
        if n and n not in text:
            items.append({"what": "새로 생기거나 바뀐 컴포넌트가 로그에 없다", "where": n})
    if re.search(r"(?m)^\s*(\d+\.\s*)?기타", text):
        items.append({"what": "「기타」 절이 있다 (공통 주제로 나눌 것)"})
    for l in text.split("영향 범위")[0].splitlines():
        if re.match(r"^[•\-*] ", l) and "//" not in l:
            items.append({"what": "변경 줄에 // 이유가 없다", "where": l[:50]})
    lint = Path.home() / ".claude" / "scripts" / "writing-lint.py"
    if lint.exists():
        out = subprocess.run([sys.executable, str(lint), str(log)], capture_output=True, text=True).stdout
        if "기계로 잡히는 항목 0건" not in out:
            m = re.search(r"— (\d+)건", out)
            items.append({"what": "writing-lint 확정 위반", "value": int(m.group(1)) if m else "?"})
    return result("G20", FAIL if items else PASS, items)


GATES = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7,
         "G8": g8, "G9": g9, "G10": g10, "G11": g11, "G12": g12, "G13": g13, "G14": g14, "G15": g15,
         "G16": g16, "G17": g17, "G18": g18, "G19": g19, "G20": g20}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in GATES:
        print(f"사용: python3 checks/gates.py <{'|'.join(GATES)}> runs/<PRD>", file=sys.stderr)
        sys.exit(64)
    out = GATES[sys.argv[1]](Path(sys.argv[2]))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit({PASS: 0, FAIL: 1, UNCOUNTABLE: 2}[out["result"]])


if __name__ == "__main__":
    main()
