// 보호 목록 서명(psig)을 가짜 노드로 검증한다. node checks/figma/test_protected_sig.mjs
import { readFileSync } from 'fs';
const src = readFileSync(new URL('./archive_snapshot.js', import.meta.url), 'utf8');
const grab = name => (src.match(new RegExp(`^function ${name}\\(.*\\}$`, 'm')) || src.match(new RegExp(`(function ${name}\\([\\s\\S]*?\\n}\\n)`)))[0];
const r = v => Math.round(v);
const fillOf = () => null;
const psig = eval('(' + grab('psig').replace(/^function psig/, 'function') + ')');
const hash = eval('(' + grab('hash').replace(/^function hash/, 'function') + ')');
const H = n => hash(psig(n, 0, true));
const clone = o => JSON.parse(JSON.stringify(o));
const text = (name, characters, x = 0, y = 0) => ({ type: 'TEXT', name, characters, width: 100, height: 20, x, y });
const inst = (name, kids, ov = 0) => ({ type: 'INSTANCE', name, width: 393, height: 852, x: 0, y: 0, overrides: Array(ov).fill({}), children: kids });
const base = { type: 'SECTION', name: '추천 레슨', width: 2000, height: 1000, x: 0, y: 0, children: [
  inst('MyForest/Diary/Details', [text('Label', '복습 시작하기')], 2),
  { type: 'FRAME', name: '_라벨', width: 393, height: 49, x: 0, y: -79, children: [text('T', '일기 상세')] } ] };
const cases = [];
let c = clone(base); c.children[0].children.push(text('Label', '롤플레이 시작하기')); c.children[0].height = 900;
cases.push(['메인 수정이 인스턴스 속으로 퍼짐', c, true]);
c = clone(base); c.children[1].children[0].characters = '일기 상세 (수정)'; cases.push(['보호 섹션 글자 직접 수정', c, false]);
c = clone(base); c.children[0].overrides.push({}); cases.push(['보호 섹션 인스턴스에 오버라이드 추가', c, false]);
c = clone(base); c.children[0].x = 50; cases.push(['보호 섹션 화면 이동', c, false]);
c = clone(base); c.children.pop(); cases.push(['보호 섹션 노드 삭제', c, false]);
let bad = 0;
for (const [name, n, same] of cases) {
  const ok = (H(n) === H(base)) === same;
  bad += !ok;
  console.log(`${ok ? 'OK ' : 'XX '} ${name} → ${same ? '같아야 함' : '달라야 함'}`);
}
console.log(`\n틀린 판정 ${bad}개`);
process.exit(bad ? 1 : 0);
