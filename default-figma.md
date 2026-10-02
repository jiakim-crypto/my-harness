# 기본값 · Figma 옮기기 (6단계)

지아가 따로 정하지 않으면 최종 와이어프레임은 아래 방식으로 Figma에 옮긴다. 출처는 `design.md`이고, 괄호 안 숫자는 그 파일의 줄 번호다. 🔸는 design.md에 없어서 클로드가 정한 값이다.

참조 파일 네 개는 `~/Desktop/언어의숲/클로드/`에 있다 🔸경로만 추가.

- `figma-components.json` · `figma-tokens.json` · `figma-screen-blocks.md` · `figma-lint.md`

## 1. 화면을 놓는 법

1. 원본 화면 인스턴스를 그대로 놓고, 바꿀 것은 4절대로 어노테이션에 적는다. 화면 옆 카드는 S5 정책 박스로만 붙인다 🔸26-10-02 지아 수정 (750의 옛 `코멘트` 카드 `36:17743`은 쓰지 않음)
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
3. 화면마다 반복되는 지시는 S5 「기본 정책」 카드 한 장에 모은다. S4에서는 카드를 만들지 않는다 🔸26-10-02 (772의 `공통 규칙` 카드 대체)
4. 자리를 바꾸는 변경은 슬롯 이름으로 적고, 무엇이 빠지는지도 같이 쓴다 (761)

## 5. 끝낼 때

1. `figma-lint.md` 검사기를 돌린다. 결과가 0이 아니면 끝난 게 아니다 (833)
2. 검사기가 잡은 값이 design.md에 적힌 값이면 고치지 않는다: 기기 그림자 · 사진 그림자 · 초록 버튼 그림자 · 잠금화면 시계 (874)
3. 지적을 하나 받으면 같은 부류를 전부 훑고, 몇 개를 고쳤는지 세어 보고한다 (789)
4. 새 지적은 고치기 전에 `figma-lint.md` 검사 규칙으로 먼저 추가한다 (837)

## 6. 텍스트 스타일 연결

새로 만든 글자는 Noto Sans KR로 들어간다. 위치·크기·정렬을 다 잡은 뒤 아래 라이브러리 스타일을 `importStyleByKeyAsync` → `setTextStyleIdAsync`로 붙인다 (26-10-02 확인, 실패 0건). 그다음 지아가 「피그마-덱힐링」 플러그인을 돌린다.

| 크기 · 굵기 | 스타일 | 키 |
|---|---|---|
| 28 Bold | typography/title_1/bold | 7d6b6e8a9439544e3142eec138b762661a982874 |
| 22 Bold | typography/title_2/bold | 42022bc589f6d1e72464778e331fa8274f31ad97 |
| 20 Bold | typography/title_3/bold | ac6df05ce7b9745e85503c8a252c64fdcf177416 |
| 17 Bold | typography/headline/bold | 3310880a08202ac737a46eb4d615b8505aba83d8 |
| 17 Regular | typography/body/regular | 97f547dcb22d5b2953096071d659c24a1a6dab0b |
| 16 Bold | typography/callout/medium | 0fb4f47c328f653910646267d5bad5dc9af02f01 |
| 16 Regular | typography/callout/regular | 8163c29c2dd6067ae6df44b126bd57d411bb796f |
| 15 Bold | typography/subheadline/medium | 097d704e292dd30d7e5d73df7e8f2b173fbe2294 |
| 15 Regular | typography/subheadline/regular | e85a5082ba3f21d3bd2b45485817c3e233089efa |
| 13 Bold | typography/footnote/medium | d443ff2fec8086293ccd2e9a2ead48172e78b6ec |
| 13 Regular | typography/footnote/regular | 780695bf22f8d2a96dfd6654f1571219e8291fd8 |
| 12 Bold | typography/caption_1/medium | 990278591be317c464aa9e960c0da00d1070b0dd |
| 11 Bold | typography/caption_2/medium | 1f74aeff0e2524f4f4f61c915e6f1e0012ca918a |
| 44 Bold (잠금화면 시계) | Display 4_44px (Pretendard) | 887e9cf824ea1e3cb9124435a0580013ebb5277a |

- 붙이지 않는 것: 캔버스 라벨, 코멘트 카드(Inter)
- 라이브러리 NanumSquareRound Bold(700)는 `…/medium`, ExtraBold(800)는 `…/bold`다

## 7. 핸드오프 섹션 배치 (26-10-02 기록 경험 개선 정리본에서 확인)

- 흐름 하나에 섹션 하나. 화면은 흐름 순서대로 왼쪽 → 오른쪽, 상태 변형은 그 화면 아래 줄
- 라벨 박스는 큰 묶음에만 단다(예: 「홈 화면 위젯 · 기록 전 → … → 내 표현」). 화면마다 달지 않는다. 레이어 이름은 `__`
- 섹션 밖에 있는 흐름을 가리켜야 하면 링크 대신 섹션 안에 복제해 그 화면 옆에 둔다

| 자리 | 값 |
|---|---|
| 섹션 안쪽 여백 | 100 |
| 라벨 높이 / 라벨과 화면 사이 | 78 / 40 |
| 화면 사이 | 120 |
| 화면과 정책 카드 사이 | 60 |
| 줄 사이 · 섹션 사이 | 240 |
| 작은 위젯 변형 사이 | 40 |

**화면 이름:** `영역/화면/상태`를 영어로 슬래시로 잇는다. 변형은 `_숫자`나 `_설명`을 붙인다. 예: `Widget/Small/BeforeStudy_1`, `WidgetGuide/Step_1`, `Notification/Unlearned_Weekly`. 라이브 페이지에 같은 화면이 있으면 그 이름을 쓴다

## 8. 이벤트 어노테이션 형식 (지아 「한국어 학습」 섹션 기준)

- Dev Mode 어노테이션, 카테고리 Development(`1:0`)
- 첫 줄 `event\_name — 트리거.`, 빈 줄, 다음 줄 `속성 prop\_name: a | b`. 밑줄은 `\_`로 쓴다
- 기존 이벤트에 속성만 더할 때: 「기존 X 이벤트에 속성 Y 추가. 새 이벤트 만들지 않음」
- 정책 카드에는 어노테이션을 달지 않는다. 카드를 복제하면 원본 카드의 어노테이션이 따라오니 지운다

