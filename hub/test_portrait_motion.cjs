const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
function harness({enabled=true,reduced=false}={}){
 const listeners={},docListeners={},calls=[],classes=new Set();
 const portrait={dataset:{},style:{},offsetTop:100,offsetHeight:200,classList:{add:(...xs)=>xs.forEach(x=>classes.add(x)),remove:(...xs)=>xs.forEach(x=>classes.delete(x))},animate:(frames,timing)=>{const a={frames,timing,canceled:false,cancel(){this.canceled=true}};calls.push(a);return a}};
 const stage={getBoundingClientRect:()=>({top:0,bottom:800})};
 const document={hidden:false,getElementById:id=>id==='mentor-art'?portrait:stage,querySelector:()=>({getBoundingClientRect:()=>({top:550})}),addEventListener:(n,f)=>docListeners[n]=f};
 const preference={matches:reduced,addEventListener:(n,f)=>listeners.preference=f};
 const window={QuestMotion:{state:{enabled}},addEventListener:(n,f)=>listeners[n]=f};
 vm.runInNewContext(fs.readFileSync('hub/static/portrait-motion.js','utf8'),{window,document,matchMedia:()=>preference,localStorage:{getItem:()=>null}});
 const state=(speaker,extra={})=>listeners['game-state']({detail:{phase:'play',chapter:4,beat:{speaker},...extra}});
 return {calls,classes,portrait,state,window,document,listeners,docListeners};
}
const h=harness();
const names=['Luma','Pip','Frost Queen Orielle','Good Witch Willow','Emberwing','Black Briar'];
const kinds=['luma','pip','queen','willow','dragon','briar'];
names.forEach((name,i)=>{h.state(name);assert.equal(h.portrait.dataset.character,kinds[i]);assert.equal(h.calls.length,i+1);assert.equal(h.calls.at(-1).frames.at(-1).opacity,1);h.state(name);assert.equal(h.calls.length,i+1)});
assert.equal(new Set(h.calls.map(x=>JSON.stringify(x.frames))).size,6);
assert.ok(h.calls.slice(0,-1).every(x=>x.canceled),'speaker switch cancels old entrance');
h.calls.at(-1).onfinish();assert.equal(h.portrait.dataset.flight,'hover');
h.window.QuestMotion.state.enabled=false;h.docListeners.change({target:{id:'motion-toggle'}});assert.equal(h.classes.size,0);
h.window.QuestMotion.state.enabled=true;h.docListeners.change({target:{id:'motion-toggle'}});assert.equal(h.calls.length,6,'motion toggle does not replay entrance');
h.document.hidden=true;h.docListeners.visibilitychange();assert.equal(h.classes.size,0);
h.document.hidden=false;h.docListeners.visibilitychange();assert.equal(h.calls.length,6,'foregrounding does not replay entrance');
h.state('Luma',{phase:'map'});assert.equal(h.classes.size,0);assert.equal(h.portrait.dataset.character,undefined);
h.state('Pip');assert.equal(h.calls.length,7);h.state('Pip',{chapter:5});assert.equal(h.calls.length,8);
const off=harness({enabled:false});off.state('Pip');assert.equal(off.calls.length,0);
const fit=harness();fit.portrait.offsetTop=400;fit.state('Pip');assert.equal(fit.portrait.style.bottom,'274px');
console.log('portrait motion ok: six distinct entrances, speaker/chapter transitions, polling dedupe, cancellation, motion-off, hidden-tab, map teardown, story clearance');
