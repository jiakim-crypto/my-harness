# 기본값 · Figma 옮기기 (6단계)

지아가 따로 정하지 않으면 최종 와이어프레임은 아래 방식으로 Figma에 옮긴다. 출처는 `design.md`이고, 괄호 안 숫자는 그 파일의 줄 번호다. 🔸는 design.md에 없어서 클로드가 정한 값이다.

참조 파일 네 개는 `~/Desktop/언어의숲/클로드/`에 있다 🔸경로만 추가.

- `figma-components.json` · `figma-tokens.json` · `figma-screen-blocks.md` · `figma-lint.md`

## 1. 화면을 놓는 법

1. 원본 화면 인스턴스를 그대로 놓고, 옆 `코멘트` 카드(`36:17743`)에 바꿀 것을 적는다 (750)
2. 393×852 완성 화면 컴포넌트 59종 중 비슷한 것이 있으면 복제해서 고친다 (856)
3. 원본을 복제했으면 이미 있는 내용은 다시 그리지 않고, 새로 더할 것만 얹는다 (756)
4. 그리기 전에 `figma-screen-blocks.md`를 열어 정보 단위마다 쓸 블록을 찾는다 (787)

## 2. 부품 찾는 순서

| 순서 | 할 일 | 실패하면 | 출처 |
|---|---|---|---|
| 1 | `figma-components.json`에서 역할로 찾는다. `importComponentSetByKeyAsync`로 가져온다 | 2로 | 793, 799 |
| 2 | `search_design_system`을 단어 하나씩 나눠 다시 검색한다 | 3으로 | 800 |
| 3 | 페이지 인스턴스의 `mainComponent.parent.name`을 모은다 | 없다고 결론 | 801 |
| 4 | 새로 그리고 「신규」라고 말한다 | | 802 |

## 3. 프레임과 값

| 항목 | 기본값 | 출처 |
|---|---|---|
| 화면 프레임 구조 | `Top` / `Body` / 하단바 세로 오토레이아웃. `Body`는 `layoutGrow=1` | 754 |
| 간격·패딩·라운드·색 | 숫자·헥사 대신 변수에 바인딩한다. 변수 ID는 `figma-tokens.json`. `fills`·`strokes`는 `setBoundVariableForPaint` | 831 |
| 상태바 | `Status Bar - iPhone` (`Background=False`) 393×54 | 826 |
| 홈 인디케이터 | `BottomCTA` 안 `Home Indicator` 393×34. CTA가 없으면 인디케이터만 | 827~829 |
| 바텀시트 | 딤 프레임 → `BottomSheet` → `Handle` + `Sheet`(패딩 8/20/20/20) + `BottomCTA` | 810 |
| 레이어 이름 | 영어 구성 단위: `Body` `Wrap` `Container` `List` `Row` `Header` `Options` / `Title` `Description` `Label` `Value` `Count` / `Icon` | 812~820 |
| 인스턴스 크기 | 바꾸지 않는다. 버튼은 라벨 길이에 맞춰 늘어난다 | 773 |
| 새 화면 텍스트 | `Noto Sans KR`로 만들고 지아가 NanumSquareRound로 바꾼다 | 846 |
| 코멘트 카드 텍스트 | Inter | 760 |

## 4. 지시를 남기는 법

1. 요소 하나를 고치라는 지시는 그 노드에 Dev Mode 어노테이션으로 단다. 문구·라벨은 Content `1:3`, 컴포넌트·변형은 Development `1:0` (764~770)
2. 변형은 전체 문자열로 적는다. 예: `Color=White · Size=L · Shape=Round · Outline=True · Type=Weak` (771)
3. 화면마다 반복되는 지시는 `공통 규칙` 카드 하나에 모은다 (772)
4. 자리를 바꾸는 변경은 슬롯 이름으로 적고, 무엇이 빠지는지도 같이 쓴다 (761)

## 5. 끝낼 때

1. `figma-lint.md` 검사기를 돌린다. 결과가 0이 아니면 끝난 게 아니다 (833)
2. 검사기가 잡은 값이 design.md에 적힌 값이면 고치지 않는다: 기기 그림자 · 사진 그림자 · 초록 버튼 그림자 · 잠금화면 시계 (874)
3. 지적을 하나 받으면 같은 부류를 전부 훑고, 몇 개를 고쳤는지 세어 보고한다 (789)
4. 새 지적은 고치기 전에 `figma-lint.md` 검사 규칙으로 먼저 추가한다 (837)
