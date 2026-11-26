const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const main=fs.readFileSync('public/index.html','utf8');
const elements={};
const defaults={days:'30',minScore:'30'};
const el=k=>elements[k]||= {
  value:defaults[k]??'',innerHTML:'', textContent:'', disabled:false,handlers:{},
  addEventListener(n,f){this.handlers[n]=f},insertAdjacentHTML(n,s){this.innerHTML+=s},
};
class SnapshotDate extends Date{constructor(...args){super(...(args.length?args:['2026-11-26T18:55:00Z']));}}
let blob, clickCount=0;
class CsvUrl extends URL {static createObjectURL(b){blob=b;return 'blob:smoke'}static revokeObjectURL(){}}
const context=vm.createContext({
  Blob,URL:CsvUrl,setTimeout:fn=>fn(),Date:SnapshotDate,
  document:{querySelector:k=>el(k.slice(1)),querySelectorAll:()=>[],body:{appendChild(){}},
    createElement(){return {click(){clickCount++},remove(){}}}},
  fetch:async url=>({json:async()=>JSON.parse(fs.readFileSync('public/'+url.split('?')[0]))}),
});
(async()=>{
  await vm.runInContext(main.match(/<script>([\s\S]+?)<\/script>/)[1],context);
  assert.match(el('count').textContent,/^0 matching permits of 219 published/);
  assert.equal(el('exportMatches').disabled,true);
  assert.match(main,/Laramie County only[\s\S]{0,150}Jackson Hole and Teton County are not covered/);
  el('showAll').handlers.click();
  assert.match(el('count').textContent,/^219 matching permits of 219 published/);
  assert.equal(el('exportMatches').disabled,false);
  assert.equal(el('pageStatus').textContent,'Page 1 of 9');
  assert.equal(el('prevPage').disabled,true);
  const firstRows=el('rows').innerHTML;
  el('nextPage').handlers.click();
  assert.notEqual(el('rows').innerHTML,firstRows);
  assert.match(el('count').textContent,/showing 26–50/);
  el('prevPage').handlers.click();
  assert.equal(el('rows').innerHTML,firstRows);
  for(let i=0;i<8;i++)el('nextPage').handlers.click();
  assert.equal(el('nextPage').disabled,true);
  assert.match(el('count').textContent,/showing 201–219/);
  el('mobileSortKey').value='issued';el('mobileSortKey').handlers.change();
  assert.equal(el('pageStatus').textContent,'Page 1 of 9');
  assert.match(el('count').textContent,/sorted by issued desc/);
  assert.match(el('rows').innerHTML,/Not reported by source/);
  el('exportMatches').handlers.click();
  assert.equal(clickCount,1);
  const report=await blob.text();
  assert.equal(report.trimEnd().split('\r\n').length,220);
  assert.match(report,/Contractor \(as reported by source\)/);
  assert.doesNotMatch(report,/"Owner"/);
  el('classification').value='SINGLE_FAMILY';el('classification').handlers.change();
  el('exportMatches').handlers.click();
  assert.equal((await blob.text()).trimEnd().split('\r\n').length,133);
  el('resetFilters').handlers.click();
  assert.match(el('count').textContent,/^0 matching permits of 219 published/);
  assert.equal(el('exportMatches').disabled,true);
  assert.equal(vm.runInContext(`safeCsvCell('  =SUM(1,2)')`,context),`"'  =SUM(1,2)"`);
  assert.equal(vm.runInContext(`safeCsvCell('abc"def')`,context),'"abc""def"');
  assert.equal(vm.runInContext(`safeCsvCell(-42)`,context),'"-42"');
  vm.runInContext('permits=Array.from({length:1002},(_,i)=>({permit_number:String(i),score:15}));showAll()',context);
  assert.match(el('count').textContent,/1,002 published · showing 1–25/);
  assert.equal(el('rows').innerHTML.match(/<tr>/g).length,25);
  el('exportMatches').handlers.click();
  assert.equal((await blob.text()).trimEnd().split('\r\n').length,1003);
  console.log('PASS: default/reset 0, Show all and export 219, filtered export 132, 1,002 total exported from paginated results, CSV cell guard');
})().catch(e=>{console.error(e);process.exitCode=1});
