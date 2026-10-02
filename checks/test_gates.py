#!/usr/bin/env python3
"""샘플로 게이트 스크립트를 검증한다. pass 샘플은 통과, fail 샘플은 실패로 판정해야 한다."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FX = HERE / "fixtures"
EXPECT = {"pass": 0, "fail": 1}


def main():
    bad = 0
    for gate_dir in sorted((d for d in FX.iterdir() if d.is_dir() and d.name[1:].isdigit()), key=lambda p: int(p.name[1:])):
        for kind in ("pass", "fail"):
            d = gate_dir / kind
            r = subprocess.run([sys.executable, str(HERE / "gates.py"), gate_dir.name, str(d)],
                               capture_output=True, text=True)
            ok = r.returncode == EXPECT[kind]
            bad += not ok
            print(f"{'OK ' if ok else 'XX '} {gate_dir.name:4} {kind:4} → 종료 코드 {r.returncode}")
            if not ok:
                print(r.stdout or r.stderr)
    print(f"\n틀린 판정 {bad}개")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
