#!/usr/bin/env python3
"""A2 승인용 표시 캡처. 와이어프레임의 data- 표시를 색으로 칠해 한 장으로 찍는다.

사용: python3 checks/overlay.py runs/<PRD>
출력: runs/<PRD>/s3/s3-markers.png

표시가 정직한지(입력이 아닌 곳에 data-input을 붙였는지, 아무 데나 data-lib를 붙였는지)는
기계가 못 가린다. 이 캡처를 A2 승인 때 지아가 한눈에 본다.
"""
import sys
from pathlib import Path

MARKS = [
    ("[data-input]", "#1a9e3f", "입력", "data-input"),
    ('[data-action="dismiss"]', "#1565e0", "닫기", "data-action"),
    ("[data-new]", "#e67700", "신규", "data-new"),
    ("[data-lib]", "#7a7a7a", "라이브러리", "data-lib"),
    ('[data-flow="diary"]', "#8a3ffc", "일기 흐름", "data-name"),
    ('[data-autostart="learning"]', "#d6002a", "자동 학습", "data-autostart"),
    ("[data-decision]", "#b58900", "형태 결정", "data-decision"),
    ("[data-recheck]", "#b58900", "되묻기", None),
]

LEGEND = "".join(
    f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px">'
    f'<i style="width:14px;height:14px;border:3px solid {c};display:inline-block"></i>{label}</span>'
    for _, c, label, _ in MARKS
)

JS = """
(marks) => {
  for (const [sel, color, label, attr] of marks) {
    for (const el of document.querySelectorAll(sel)) {
      el.style.outline = `3px solid ${color}`;
      el.style.outlineOffset = '-1px';
      const tag = document.createElement('div');
      const v = attr ? el.getAttribute(attr) : '';
      tag.textContent = v && v !== '' && v !== 'true' ? `${label}: ${v}` : label;
      tag.style.cssText = `position:absolute;z-index:99999;background:${color};color:#fff;font:700 11px/1.4 -apple-system,sans-serif;padding:1px 5px;border-radius:3px;white-space:nowrap;pointer-events:none`;
      const r = el.getBoundingClientRect();
      tag.style.left = (r.left + window.scrollX) + 'px';
      tag.style.top = (r.top + window.scrollY - 16) + 'px';
      document.body.appendChild(tag);
    }
  }
}
"""


def main():
    if len(sys.argv) != 2:
        print("사용: python3 checks/overlay.py runs/<PRD>", file=sys.stderr)
        sys.exit(64)
    run = Path(sys.argv[1])
    wf = run / "s3" / "s3-wireframe.html"
    if not wf.exists():
        print(f"{wf}가 없다", file=sys.stderr)
        sys.exit(2)
    out = run / "s3" / "s3-markers.png"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1400, "height": 1000})
        pg.goto(wf.resolve().as_uri())
        pg.wait_for_timeout(300)
        pg.evaluate("""(html) => { const d = document.createElement('div');
          d.innerHTML = html; d.style.cssText = 'position:sticky;top:0;z-index:100000;background:#fff;border-bottom:1px solid #ccc;padding:10px 16px;font:600 13px -apple-system,sans-serif';
          document.body.prepend(d); }""", "<div style='margin-bottom:6px'>표시 캡처 · 게이트는 아래 이름표만 센다. 이름표가 제자리에 붙었는지 본다: 입력은 사진·글을 넣는 곳, 닫기는 ✕, 라이브러리는 실제 앱 부품을 그대로 쓴 곳</div>" + LEGEND)
        counts = pg.evaluate("(sels) => sels.map(s => document.querySelectorAll(s).length)", [m[0] for m in MARKS])
        pg.evaluate(JS, [list(m) for m in MARKS])
        pg.screenshot(path=str(out), full_page=True)
        b.close()
    print(out)
    for (sel, _, label, _), n in zip(MARKS, counts):
        print(f"  {label:6} {n}개")


if __name__ == "__main__":
    main()
