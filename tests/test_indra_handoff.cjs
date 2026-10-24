/* INDRA starts a new editable brief through the existing Fabbrica planner. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const source = name => fs.readFileSync(path.join(__dirname, '..', 'public', name), 'utf8');
const tick = () => new Promise(resolve => setTimeout(resolve, 20));

async function scenario({url, unavailable = false, submit = false, expectMission = true}) {
  const errors = [];
  const output = new VirtualConsole();
  output.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(source('fabbrica.html'), {
    url, runScripts:'outside-only', virtualConsole:output
  });
  const w = dom.window;
  const $ = id => w.document.getElementById(id);
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.eval(source('fabbrica-examples.js'));
  const priorId = 'a'.repeat(32);
  const plan = JSON.parse(JSON.stringify(w.FABBRICA_LEVELS[1]));
  const old = {id:priorId, status:'complete', version:1, plan,
    brief:{dream:'Un desiderio precedente da conservare.', city:'Bruxelles'},
    expires_at:'2026-11-14T10:00:00Z'};
  const calls = [];
  w.fetch = async (uri, options = {}) => {
    calls.push({uri, method:options.method || 'GET', body:options.body});
    if (uri.endsWith('/status')) {
      if (unavailable) throw new Error('offline');
      return {ok:true,json:async()=>({ai_available:true,latest_id:priorId})};
    }
    if (options.method === 'POST') return {ok:true,json:async()=>({
      ...old,id:'b'.repeat(32),brief:JSON.parse(options.body)
    })};
    return {ok:true,json:async()=>structuredClone(old)};
  };
  w.eval(source('fabbrica.js'));
  // A delayed status response must not overwrite an already edited mission.
  if (expectMission) {
    assert.match($('dream-text').value, /Missione INDRA 001/);
    $('dream-city').value = 'Luogo scelto dal partecipante';
  }
  await tick();
  assert.deepEqual(errors, []);
  assert.equal(calls.filter(c=>c.method!=='GET').length,0,'opening never generates or writes a plan');
  if (expectMission) {
    assert.equal($('copione').hidden,true);
    assert.equal(calls.filter(c=>c.uri.includes('/plans/')).length,0,'do not reopen a prior plan over the mission');
    assert.equal($('dream-city').value,'Luogo scelto dal partecipante');
    assert.equal($('dream-budget').value,'Da definire');
    assert.ok($('dream-text').value.length <= 2500);
    assert.ok($('dream-time').value.length <= 100);
    assert.ok($('dream-delegation').value.length <= 800);
    if (submit) {
      $('dream-text').value += ' Organizzatore scelto: il facilitatore del gruppo.';
      $('generate-button').click();
      await tick();
      const writes=calls.filter(c=>c.method==='POST');
      assert.equal(writes.length,1);
      assert.equal(writes[0].uri,'/api/fabbrica/plans');
      const brief=JSON.parse(writes[0].body);
      assert.match(brief.dream,/Organizzatore scelto/);
      assert.equal(brief.parent_id,undefined,'a mission does not revise an unrelated plan');
      assert.equal($('copione').hidden,false);
    }
  } else {
    assert.equal($('dream-text').value,old.brief.dream,'standard reopening and direct plan links retain their behavior');
    assert.equal($('copione').hidden,false);
  }
  assert.deepEqual(errors, []);
  w.close();
}

(async()=>{
  const page=new JSDOM(source('indra.html'),{url:'https://example.test/indra'});
  const entry=page.window.document.querySelector('a.mission-link').href;
  assert.equal(new URL(entry).pathname,'/fabbrica');
  await scenario({url:entry,submit:true});
  await scenario({url:entry,unavailable:true});
  await scenario({url:'https://example.test/fabbrica?missione=unknown',expectMission:false});
  await scenario({url:'https://example.test/fabbrica?missione=%3Cscript%3E',expectMission:false});
  await scenario({url:'https://example.test/fabbrica',expectMission:false});
  await scenario({url:'https://example.test/fabbrica?missione=indra-001#copione/'+'a'.repeat(32),expectMission:false});
  page.window.close();
  console.log('PASS: INDRA link, editable draft, explicit generation, prior-plan preservation, unavailable service, allowlist and direct-plan precedence');
})().catch(error=>{console.error(error);process.exitCode=1;});
