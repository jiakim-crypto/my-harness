#!/usr/bin/env python3
"""PreToolUse 훅. 하위 에이전트가 자기 단계 폴더 밖 파일을 쓰거나 고치면 막는다.

- 에이전트 이름(agent_type)은 훅 입력에 들어온다. 오케스트레이터(메인 세션)는 agent_type이 없어 통과한다
- judge는 어떤 파일도 쓸 수 없다
- 막을 때는 종료 코드 2와 이유를 stderr로 돌려준다
"""
import json
import re
import sys

ALLOWED = {
    "brief": r"runs/[^/]+/s1/",
    "prd": r"runs/[^/]+/s2/",
    "screen": r"runs/[^/]+/s3/",
    "figma": r"runs/[^/]+/s4/",
    "policy": r"runs/[^/]+/s5/",
    "archive": r"runs/[^/]+/s6/",
    "judge": None,
}


def main():
    data = json.load(sys.stdin)
    agent = data.get("agent_type")
    if agent not in ALLOWED:
        sys.exit(0)
    ti = data.get("tool_input", {})
    path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    rule = ALLOWED[agent]
    if rule is None:
        print(f"judge는 파일을 쓸 수 없다: {path}", file=sys.stderr)
        sys.exit(2)
    if agent == "archive" and re.search(r"snapshot-[^/]*\.json$", path):
        print(f"snapshot 파일은 오케스트레이터만 쓴다. 막은 경로: {path}", file=sys.stderr)
        sys.exit(2)
    if not re.search(rule, path):
        folder = rule.replace("[^/]+", "<PRD>")
        print(f"{agent} 에이전트는 {folder} 안에만 쓸 수 있다. 막은 경로: {path}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
