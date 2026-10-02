#!/usr/bin/env python3
"""design.md의 색을 impeccable 훅이 읽는 값 목록(.impeccable/design.json)에 채운다.

훅은 design.md 맨 위의 colors·rounded·typography만 읽는다. doc-light·doc-dark·os-ios·app-colors와
본문에만 적힌 사진 자리 색의 어두운 끝 값은 이 스크립트로 design.json colorMeta에 넣어야 오탐이 안 난다.
이미 있는 값은 건드리지 않고, 빠진 값만 더한다. design.md를 고친 뒤 다시 돌린다.

사용: python3 checks/sync_design_sidecar.py
"""
import json
import re
from pathlib import Path

import yaml

CLAUDE_DIR = Path.home() / "Desktop" / "언어의숲" / "클로드"  # 다른 컴퓨터에서도 같은 자리에 둔다 (SETUP.md)
DESIGN_MD = CLAUDE_DIR / "DESIGN.md"
SIDECAR = CLAUDE_DIR / ".impeccable" / "design.json"
GROUPS = ["colors", "doc-light", "doc-dark", "os-ios", "app-colors"]


def norm(v):
    return v.strip().lower()


def main():
    text = DESIGN_MD.read_text()
    front = yaml.safe_load(text.split("---", 2)[1])
    side = json.loads(SIDECAR.read_text())
    meta = side.setdefault("extensions", {}).setdefault("colorMeta", {})

    have = set()
    for m in meta.values():
        if isinstance(m, dict):
            if isinstance(m.get("canonical"), str):
                have.add(norm(m["canonical"]))
            for v in m.get("tonalRamp", []) or []:
                if isinstance(v, str):
                    have.add(norm(v))

    added = []
    for g in GROUPS:
        for k, v in (front.get(g) or {}).items():
            if not isinstance(v, str) or norm(v) in have:
                continue
            name = f"{g}-{k}" if g != "colors" else k
            meta[name] = {"canonical": v, "role": g, "purpose": f"design.md {g}.{k}"}
            have.add(norm(v))
            added.append(f"{name} {v}")

    # 본문 Placeholder 절: 「(`#밝은쪽` → `#어두운쪽`)」의 어두운 쪽
    for light, dark in re.findall(r"`(#[0-9a-fA-F]{6})` → `(#[0-9a-fA-F]{6})`", text):
        if norm(dark) in have:
            continue
        meta[f"placeholder-end-{dark[1:]}"] = {"canonical": dark, "role": "placeholder", "purpose": f"사진 자리 그라데이션 어두운 끝 ({light} → {dark})"}
        have.add(norm(dark))
        added.append(f"placeholder-end {dark}")

    SIDECAR.write_text(json.dumps(side, ensure_ascii=False, indent=2) + "\n")
    print(f"더한 색 {len(added)}개")
    for a in added:
        print("  ", a)


if __name__ == "__main__":
    main()
