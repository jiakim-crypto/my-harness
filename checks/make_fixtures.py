#!/usr/bin/env python3
"""게이트마다 통과 샘플 1개, 실패 샘플 1개를 checks/fixtures/ 아래에 만든다."""
import json
import shutil
from pathlib import Path

FX = Path(__file__).resolve().parent / "fixtures"

CSS = """
body{margin:0;background:#eef1ec;font-family:'NanumSquareRound','Pretendard',sans-serif;color:#20211f}
.screen{width:393px;height:852px;background:#fbfffa;display:flex;flex-direction:column}
.sb{height:54px}
.hi{height:34px}
.body{flex:1;display:flex;flex-direction:column;gap:12px;padding:20px}
.title{font-size:22px;font-weight:800;color:#20211f}
.txt{font-size:15px;font-weight:400;color:#434542}
.btn{background:#135000;color:#b7ff8d;border-radius:16px;padding:8px 20px;font-size:16px;font-weight:700;height:40px}
.chip{background:#1350001f;color:#135000;border-radius:100px;padding:4px 8px;font-size:12px;font-weight:700}
.doc{font-size:12.5px;color:rgba(0,0,0,.45)}
"""


def page(screen_body, extra_css="", doc=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}{extra_css}</style></head><body>
<div class="screen" data-screen="오늘의 표현" data-after="capture">
  <div class="sb" data-part="statusbar"></div>
  <div class="body" data-flow="diary" data-name="위젯으로 찍기">
{screen_body}
  </div>
  <div class="hi" data-part="home-indicator"></div>
</div>
{doc}
</body></html>"""


GOOD_BODY = """    <div class="title">오늘의 표현</div>
    <div class="chip" data-input="photo">사진 찍기</div>
    <div class="txt">grab a bite</div>
    <div class="txt" data-action="dismiss">닫기</div>
    <div class="btn">배우기</div>"""

GOOD_DOC = """<p class="doc" data-decision="배우기 버튼 형태">근거: Apple HIG Buttons, 화면 하단 주 행동은 전체 폭 버튼</p>
<p class="doc" data-recheck>찍은 사람이 닫기와 배우기 중 고를 수 있다. 목표(원할 때 배우기)가 달성된다</p>"""

REFS_OK = """| 화면 | 출처 | 무드/용도 | 여기서 빌릴 것 |
|---|---|---|---|
| 오늘의 표현 | UI Bowl · 토스 | 용도 | 하단 주 버튼과 닫기를 한 화면에 두는 배치 |
"""

REFS_BAD = """| 화면 | 출처 | 무드/용도 | 여기서 빌릴 것 |
|---|---|---|---|
| 미학습 목록 | Pinterest | 분위기 | |
"""


def write(gate, kind, files, state=None):
    d = FX / gate / kind
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    if state is not None:
        (d / "state.json").write_text(json.dumps(state, ensure_ascii=False))


def main():
    if FX.exists():
        shutil.rmtree(FX)
    good = page(GOOD_BODY, doc=GOOD_DOC)
    rec = {"record_feature": True}

    # G4 레퍼런스
    write("G4", "pass", {"s3/s3-wireframe.html": good, "s3/s3-refs.md": REFS_OK})
    write("G4", "fail", {"s3/s3-wireframe.html": good, "s3/s3-refs.md": REFS_BAD})

    # G5 값이 표 안에 있나
    write("G5", "pass", {"s3/s3-wireframe.html": good})
    bad5 = page(GOOD_BODY.replace('class="txt">grab', 'class="txt" style="color:#333333;font-size:14px;border-radius:14px;padding:5px">grab'), doc=GOOD_DOC)
    write("G5", "fail", {"s3/s3-wireframe.html": bad5})

    # G6 신규 컴포넌트 목록
    new_el = GOOD_BODY + '\n    <div data-new="사진 스택 카드" style="border-radius:13px;padding:7px;background:#abcdef">스택</div>'
    wf6 = page(new_el, doc=GOOD_DOC)
    write("G6", "pass", {"s3/s3-wireframe.html": wf6,
                          "s3/s3-new.md": "| 이름 | 이유 |\n|---|---|\n| 사진 스택 카드 | 하루 여러 장을 겹쳐 보여줄 부품이 라이브러리에 없다 |\n"})
    write("G6", "fail", {"s3/s3-wireframe.html": wf6})

    # G7 조립 규칙·근거·되묻기
    lib = GOOD_BODY + '\n    <div data-lib="DiaryCard"><div style="font-size:28px;font-weight:800;color:#0000004d">16</div></div>'
    write("G7", "pass", {"s3/s3-wireframe.html": page(lib, doc=GOOD_DOC)})
    bad7_body = GOOD_BODY.replace('<div class="title">오늘의 표현</div>',
                                  '<div class="title">오늘의 표현</div>\n    <div class="title">두 번째 큰 제목</div>\n    <div class="btn" style="height:120px">초록 면 하나 더</div>')
    bad7_doc = '<p class="doc" data-decision="배우기 버튼 형태">예뻐서 골랐다</p>'
    write("G7", "fail", {"s3/s3-wireframe.html": page(bad7_body, doc=bad7_doc)})

    # G13 ★ 어기면 안 되는 것
    write("G13", "pass", {"s3/s3-wireframe.html": good,
                           "s2/s2-prd.md": "## 범위\n사진을 찍으면 오늘의 표현이 생긴다.\n\n## Out of Scope\n| 하루 요약 문장 생성 | 본인이 쓴 것이 사라진다 | 안 함 |\n"},
          state=rec)
    bad13_body = GOOD_BODY.replace(' data-input="photo"', "").replace(' data-action="dismiss"', "")
    write("G13", "fail", {"s3/s3-wireframe.html": page(bad13_body, doc=GOOD_DOC),
                           "s2/s2-prd.md": "## 범위\n자정에 AI가 하루를 한 문장으로 요약해 일기로 남긴다.\n"},
          state=rec)

    # G1 숫자마다 쿼리 번호
    ana = "| 번호 | 이벤트 | 분모 | 기간 | 결과 | 재실행 |\n|---|---|---|---|---|---|\n| Q1 | generate_expressions_completed 2회 | 신규 가입자 | 9/02~9/15 | 100명 중 36명 | 100명 중 36명 |\n"
    write("G1", "pass", {"s2/s2-analysis.md": ana,
                          "s2/s2-prd.md": "# PRD\n\n## 배경\n첫 일기를 쓴 100명 중 36명이 두 번째를 쓴다 [Q1].\n\n## 문서점검 9개\n1. 결론 먼저다\n"})
    write("G1", "fail", {"s2/s2-analysis.md": ana.replace("| 9/02~9/15 |", "|  |"),
                          "s2/s2-prd.md": "# PRD\n\n## 배경\n첫 일기를 쓴 100명 중 36명이 두 번째를 쓴다.\n두 번째를 쓴 사람의 52%가 세 번째를 쓴다 [Q7].\n"})

    # G2 문체 검사 + 문서점검 9줄
    nine = "\n".join(f"{i}. 확인했다" for i in range(1, 10))
    write("G2", "pass", {"s2/s2-prd.md": f"# 위젯으로 찍기\n\n## 배경\n사용자는 밤에 앱을 연다.\n\n## 문서점검 9개\n{nine}\n"})
    write("G2", "fail", {"s2/s2-prd.md": "# 위젯으로 찍기\n\n## 배경\n사용자는 밤에 앱을 연다.\n\n## 문서점검 9개\n1. 확인했다\n2. 확인했다\n"})

    # G3 리뷰 지적 수 = 로그 항목 수, 5칸
    entry = "### #9 — 위젯 PRD · 대안 공백\n\n| 칸 | 내용 |\n|---|---|\n| 지적 원문 | 알림만 늘리면 안 되나요? |\n| 내 원래 논리 | 찍는 때를 옮긴다 |\n| 뛴 지점 | 알림 대안을 안 봤다 |\n| 유형 | 대안 공백 |\n| 다음에 걸 질문 | 더 싼 방법 두 개를 댈 수 있나? |\n"
    write("G3", "pass", {"s2/logic-review.md": "사전 검사 결과 1건", "s2/review-comments.md": "1. 알림만 늘리면 안 되나요?\n", "s2/log-draft.md": entry})
    write("G3", "fail", {"s2/review-comments.md": "1. 알림만 늘리면 안 되나요?\n2. 표본이 작아요\n", "s2/log-draft.md": entry.replace("더 싼 방법 두 개를 댈 수 있나?", "")})

    # G8 · G9 Figma 검사 결과와 컨펌 표
    fig_ok = "Figma: https://www.figma.com/design/x\n\nfigma-lint 결과: 0\n신규 표시 없는 새 부품: 0\n\n| 번호 | 지적 | 반영/보류 | 보류 이유 | 같은 부류 고친 개수 | 게이트가 미리 잡았나 |\n|---|---|---|---|---|---|\n| 1 | 버튼이 두 개라 헷갈린다 | 반영 | | 3 | 아니오 |\n| 2 | 사진 크기 | 보류 | 실제 사진으로 다시 본다 | 0 | 예 |\n"
    write("G8", "pass", {"s4/s4-figma.md": fig_ok})
    write("G8", "fail", {"s4/s4-figma.md": fig_ok.replace("figma-lint 결과: 0", "figma-lint 결과: 4")})
    write("G9", "pass", {"s4/s4-figma.md": fig_ok})
    write("G9", "fail", {"s4/s4-figma.md": fig_ok.replace("| 보류 | 실제 사진으로 다시 본다 | 0 | 예 |", "| 보류 | | 몇 개 | 모름 |")})

    # G10 · G11 · G12 정책 카드
    write("G10", "pass", {"s5/s5-handoff.md": "figma-lint 14번: 0\n"})
    write("G10", "fail", {"s5/s5-handoff.md": "figma-lint 14번: 2\n"})
    cards = "| 화면 | 블록 | 문장 | PRD 링크 |\n|---|---|---|---|\n| 위젯 ① | 분기 | 오늘 일기 없음 → 찍어두기 노출 | [5-1](https://app.notion.com/p/x#5-1) |\n| 위젯 ② | 값 | 뜻 상한 7자 | [5-1](https://app.notion.com/p/x#5-1) |\n"
    write("G11", "pass", {"s5/s5-policy-cards.md": cards})
    write("G11", "fail", {"s5/s5-policy-cards.md": cards.replace("뜻 상한 7자", "뜻 상한 7자. 길면 잘리기 때문에 대안을 검토함")})
    write("G12", "pass", {"s5/s5-policy-cards.md": cards})
    write("G12", "fail", {"s5/s5-policy-cards.md": cards.replace("[5-1](https://app.notion.com/p/x#5-1) |\n| 위젯 ②", " |\n| 위젯 ②")})
    print(f"만든 샘플: {sum(1 for _ in FX.glob('*/*'))}개 → {FX}")


if __name__ == "__main__":
    main()
