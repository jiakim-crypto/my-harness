# 다른 컴퓨터에서 쓰기

git에는 하네스의 규칙·에이전트·게이트만 들어 있다. 하네스가 기대는 파일 몇 가지는 git 밖에 있어서, 새 컴퓨터에서는 아래 순서로 갖춘다. 끝나면 `python3 checks/doctor.py`가 「빠진 것 0개」를 보여야 한다.

## git에 있는 것 · 없는 것

| 구분 | 무엇 | 새 컴퓨터에서 |
|---|---|---|
| git에 있음 | 규칙(`rules.md` 등) · 에이전트(`.claude/agents/`) · 게이트(`checks/`) · 기본값 파일 | `git clone`으로 받는다 |
| git에서 뺌 | `runs/`(실행 기록) · `prd.md` | 필요하면 따로 옮긴다. 새로 시작하면 없어도 된다 |
| git 밖 · 클로드 폴더 | DESIGN.md · figma-lint.md · 문서점검.md · 논리점프 로그 · Figma 부품 목록 | `~/Desktop/언어의숲/클로드`에 둔다. 지금 Mac은 iCloud가 데스크톱을 동기화한다. 새 컴퓨터에서 같은 Apple ID로 로그인하면 이 폴더가 `~/Desktop/언어의숲/클로드`로 내려받아진다 |
| git 밖 · 내 Claude 설정 | `~/.claude/scripts/writing-lint.py` · `~/.claude/skills/`(logic-review, english-forest-figma-versioning 등) | 폴더째 복사한다 |
| git 밖 · 이 컴퓨터 전용 값 | `local.md` (회사 Figma 파일 키). 공개 저장소라 git에서 뺐다 | 옛 컴퓨터에서 복사하거나 같은 표 형식으로 새로 만든다 |
| git 밖 · 연결 | Claude 앱 커넥터(Figma · Notion · Mixpanel · UI Bowl) | 새 컴퓨터의 Claude 앱에서 다시 연결한다 |

## 순서

1. Claude 데스크톱 앱을 설치하고 로그인한다. 커넥터 네 개를 연결한다
2. `git clone https://github.com/jiakim-crypto/my-harness.git ~/Desktop/my-harness`
3. 클로드 폴더가 `~/Desktop/언어의숲/클로드`에 있는지 본다 (iCloud 동기화를 기다리거나 복사)
4. `~/.claude/scripts/`와 `~/.claude/skills/`를 옛 컴퓨터에서 복사한다
5. `python3 checks/doctor.py`를 돌려, 빠진 것마다 나오는 한 줄 명령을 따른다. 바로가기 3개(`design.md`, `.impeccable/` 두 개)는 여기서 다시 만든다
6. `python3 checks/test_gates.py`가 「틀린 판정 0개」인지 본다
7. Claude 앱에서 `~/Desktop/my-harness` 폴더로 새 세션을 연다. 다른 폴더에서 연 세션을 옮겨 오면 폴더 제한 훅은 git 최상위 폴더를 찾아 그대로 돈다

## 주의

- 한 번에 한 컴퓨터에서만 고친다. 이 폴더도 iCloud 데스크톱 안에 있어서, 두 컴퓨터가 동시에 고치면 `.git`이 꼬일 수 있다. 한쪽에서 끝내고 push한 뒤 다른 쪽에서 pull한다
- Figma 앱에 「Missing font」가 뜨면 앱을 재시작한다. Replace fonts는 누르지 않는다 (`figma-notes.md`)
