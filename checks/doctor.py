#!/usr/bin/env python3
"""이 컴퓨터에서 하네스를 돌릴 준비가 됐는지 본다. 사용: python3 checks/doctor.py

하네스 파일(규칙·에이전트·게이트)은 git에 있지만, 아래는 git 밖에 있어 컴퓨터마다 따로 갖춰야 한다.
빠진 것마다 고치는 법을 한 줄로 알려준다. 판정은 하지 않는다.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
CLAUDE_DIR = HOME / "Desktop" / "언어의숲" / "클로드"

CHECKS = [
    # (무엇, 경로, 고치는 법)
    ("클로드 폴더", CLAUDE_DIR, "언어의숲/클로드 폴더를 ~/Desktop/언어의숲/클로드 에 둔다 (동기화 드라이브에서 받기)"),
    ("DESIGN.md", CLAUDE_DIR / "DESIGN.md", "클로드 폴더를 받는다"),
    ("figma-lint.md", CLAUDE_DIR / "figma-lint.md", "클로드 폴더를 받는다"),
    ("문서점검.md", CLAUDE_DIR / "문서점검.md", "클로드 폴더를 받는다"),
    ("논리점프_로그.md", CLAUDE_DIR / "논리점프_로그.md", "클로드 폴더를 받는다"),
    ("figma-components.json", CLAUDE_DIR / "figma-components.json", "클로드 폴더를 받는다"),
    ("concept-seed.mjs", CLAUDE_DIR / ".claude/skills/impeccable/scripts/concept-seed.mjs", "클로드 폴더의 .claude/skills 까지 받는다"),
    ("local.md (Figma 파일 키)", ROOT / "local.md", "옛 컴퓨터에서 local.md 를 복사한다 (SETUP.md)"),
    ("문체 검사기", HOME / ".claude/scripts/writing-lint.py", "~/.claude/scripts/writing-lint.py 를 복사한다"),
    ("logic-review 스킬", HOME / ".claude/skills/logic-review/SKILL.md", "~/.claude/skills/logic-review 를 복사한다"),
    ("figma-versioning 스킬", HOME / ".claude/skills/english-forest-figma-versioning/SKILL.md", "~/.claude/skills/english-forest-figma-versioning 을 복사한다"),
]
LINKS = [
    ("design.md 바로가기", ROOT / "design.md", CLAUDE_DIR / "DESIGN.md"),
    (".impeccable/config.json 바로가기", ROOT / ".impeccable/config.json", CLAUDE_DIR / ".impeccable/config.json"),
    (".impeccable/design.json 바로가기", ROOT / ".impeccable/design.json", CLAUDE_DIR / ".impeccable/design.json"),
]
TOOLS = [("python3", "python3 --version"), ("node", "node --version"), ("git", "git --version")]
PY_MODULES = [("yaml", "pip3 install pyyaml"), ("playwright", "pip3 install playwright && python3 -m playwright install chromium")]


def main():
    bad = 0
    print("## 파일")
    for name, p, fix in CHECKS:
        ok = p.exists()
        bad += not ok
        print(f"{'OK ' if ok else 'XX '} {name}" + ("" if ok else f"  → {fix}"))
    print("\n## 바로가기 (다른 컴퓨터에서는 다시 만든다)")
    for name, link, target in LINKS:
        ok = link.exists() and link.resolve() == target.resolve()
        bad += not ok
        print(f"{'OK ' if ok else 'XX '} {name}" + ("" if ok else f"  → ln -sf \"{target}\" \"{link}\""))
    print("\n## 프로그램")
    for name, cmd in TOOLS:
        ok = shutil.which(name) is not None
        bad += not ok
        print(f"{'OK ' if ok else 'XX '} {name}" + (f"  ({subprocess.run(cmd.split(), capture_output=True, text=True).stdout.strip()})" if ok else "  → 설치"))
    for mod, fix in PY_MODULES:
        try:
            __import__(mod)
            print(f"OK  python {mod}")
        except ImportError:
            bad += 1
            print(f"XX  python {mod}  → {fix}")
    print("\n## 손으로 확인할 것 (스크립트가 못 본다)")
    print("- Claude 앱 커넥터: Figma · Notion · Mixpanel · UI Bowl 이 연결돼 있다")
    print("- Figma 데스크톱 앱에 NanumSquareRound 글꼴이 보인다 (Missing font 창이 뜨면 재시작)")
    print(f"\n빠진 것 {bad}개")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
