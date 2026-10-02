# 산출물

PRD 하나마다 runs/<PRD 제목>-v<버전>/ 폴더 하나에 모든 산출물을 두고, 안에 단계별 폴더 s1~s5를 둔다. 예: runs/기록경험개선-v1.1/s2/s2-prd.md

## 폴더 이름

- S1 멈춤에서 지아가 고른 문제와 PRD 이름을 함께 준다
- 이름을 받기 전 S1 산출물은 runs/_draft-<YYMMDD>/에 두고, 이름을 받으면 폴더를 옮긴다
- 한 PRD에 기능이 여러 개면 와이어프레임 한 파일 안에서 기능별로 절을 나눈다

## 단계별 파일

| 단계 | 파일 | 담는 것 |
|---|---|---|
| S1 | s1-brief.md | 눈에 띈 데이터 후보와 원출처 |
| S2 | s2-analysis.md | 쿼리, 이벤트, 분모, 기간, 결과 숫자 |
| S2 | s2-prd.md | PRD 작업본 |
| S3 | s3-refs.md | 레퍼런스마다 출처와 「여기서 빌릴 것」 한 줄 |
| S3 | s3-edge-cases.md | 엣지케이스 점검표 (분류 · 케이스 · 처리) |
| S3 | s3-wireframe.html | 와이어프레임 |
| S3 | s3-markers.png | A2용 표시 캡처 (checks/overlay.py가 만든다) |
| S4 | s4-figma.md | Figma 링크, figma-lint 결과, 컨펌 코멘트 목록 |
| S5 | s5-layout.md | 프레임 정리 기준과 간격 숫자 |
| S5 | s5-policy-cards.md | 정책 카드 문안 (카드 형식) |
| S5 | s5-handoff.md | 핸드오프 링크와 FE·BE 전달 내용 |
| 전체 (PRD 폴더 바로 아래) | state.json | 지금 단계, 게이트 결과, 게이트별 실패 횟수, 기다리는 입력 |

## 규칙 파일

- 게이트 G1~G12 조건, 실패 3번 규칙, 되돌아가는 지점은 rules.md 하나에 둔다. 판정 스크립트는 rules.md만 읽는다
- 디자인 값은 design.md와 default-*.md에 두고, rules.md는 그 파일을 가리킨다
- story-work.md에는 AS-IS 기록만 남긴다

## 원본 위치

| 결과물 | 원본 | 로컬 파일 |
|---|---|---|
| PRD | 노션 PRD DB | s2-prd.md는 작업본. S2 게이트 통과 뒤 지아에게 묻고 노션에 올린다 |
| 시안 | Figma | s4-figma.md에 링크와 검사 결과만 |
| figma-lint.md, 논리점프_로그.md | 클로드/ 폴더 | 복사하지 않고 참조한다 |

## 이어서 하기

「이어서 해줘」라고 하면 state.json을 읽고 멈춘 단계부터 다시 한다. 멈춤에서 기다리는 동안 세션을 닫아도 된다. 레퍼런스 이미지는 다시 붙여야 한다.

## 아카이브 산출물

아카이브 한 번마다 runs/<기능>-archive-<YYMMDD>/ 폴더 하나를 두고, 안에 s6/ 폴더와 state.json을 둔다. 예: runs/롤플레이S1-archive-261002/s6/s6-impact.md

| 단계 | 파일 | 담는 것 |
|---|---|---|
| S6-1 | s6-impact.md | 표 `화면 \| 핸드오프 노드 \| 기존 메인 \| 처리 \| 바뀐 노드 수 \| 영향 인스턴스 수 \| 이유`. 처리는 「메인 수정」·「컴포넌트로 만들기」·「새 컴포넌트」·「라이브러리 수정」·「해당 없음」 중 하나. 남길 중첩 섹션은 두 번째 표 `남길 묶음 \| 이유` |
| S6-1 | snapshot-before.json | 고치기 전 상태. checks/figma/archive_snapshot.js 출력 |
| S6-2 | snapshot-after.json | 고친 뒤 상태. 같은 스크립트 출력 |
| S6-3 | snapshot-final.json | 옮긴 뒤 FullScreen 섹션 배치. 같은 스크립트 출력 |
| S6-4 | s6-library-log.md | 버전 히스토리 본문 (english-forest-figma-versioning 형식) |
| 폴더 바로 아래 | state.json | 지금 단계, 게이트 결과, A3 승인, 고친 메인 id 목록 |

- 게이트 G16~G20 조건은 rules.md에 둔다. 배치값은 default-archive.md에 둔다
- snapshot 파일은 오케스트레이터가 고정 스크립트를 돌려 저장한다. 에이전트는 읽기만 한다
- 「이어서 해줘」라고 하면 state.json의 고친 메인 id 목록부터 읽고, 목록에 없는 메인부터 이어서 고친다
