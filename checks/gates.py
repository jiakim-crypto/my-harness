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
        big = [e for e in scr["els"] if e["text"] and not e["isLib"] and px(e["fontSize"]) in (28.0, 22.0)]
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


REASON = re.compile(r"왜냐하면|때문에|때문이|검토|대안|고민")


def _cards(run):
    p = run / "s5" / "s5-policy-cards.md"
    if not p.exists():
        return None
    head, rows = md_table(p, ["화면", "블록", "문장", "PRD 링크"])
    return rows if head else None


def g11(run):
    rows = _cards(run)
    if rows is None:
        return result("G11", UNCOUNTABLE, note="s5-policy-cards.md에 「화면 | 블록 | 문장 | PRD 링크」 표가 없다")
    items = [{"what": "카드에 이유 표현", "where": col(r, "화면"), "value": col(r, "문장")[:60]}
             for r in rows if REASON.search(col(r, "문장"))]
    return result("G11", FAIL if items else PASS, items)


def g12(run):
    rows = _cards(run)
    if rows is None:
        return result("G12", UNCOUNTABLE, note="s5-policy-cards.md에 「화면 | 블록 | 문장 | PRD 링크」 표가 없다")
    items = [{"what": "PRD 절 링크가 없는 카드", "where": col(r, "화면"), "value": col(r, "문장")[:60]}
             for r in rows if not re.search(r"https?://|\]\(", col(r, "PRD 링크"))]
    return result("G12", FAIL if items else PASS, items)


GATES = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7,
         "G8": g8, "G9": g9, "G10": g10, "G11": g11, "G12": g12, "G13": g13}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in GATES:
        print(f"사용: python3 checks/gates.py <{'|'.join(GATES)}> runs/<PRD>", file=sys.stderr)
        sys.exit(64)
    out = GATES[sys.argv[1]](Path(sys.argv[2]))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit({PASS: 0, FAIL: 1, UNCOUNTABLE: 2}[out["result"]])


if __name__ == "__main__":
    main()
