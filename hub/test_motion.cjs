const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source=fs.readFileSync(path.join(__dirname,'static','motion.js'),'utf8');
class Target {
  constructor(tag='div') {this.tagName=tag;this.listeners={};this.children=[];this.attributes={};this.readyState=0;this.paused=true;this.loadCalls=0;this.playCalls=0;this.currentTime=0;this.classList={s:new Set(),add(...x){x.forEach(v=>this.s.add(v));},remove(...x){x.forEach(v=>this.s.delete(v));},toggle(x,yes){if(yes)this.s.add(x);else this.s.delete(x);},contains(x){return this.s.has(x);}};this.style={setProperty(){}};}
  addEventListener(name,fn){(this.listeners[name] ||= []).push(fn);}
  emit(name,detail){(this.listeners[name]||[]).forEach(fn=>fn({detail}));}
  setAttribute(name,val){this.attributes[name]=val;}
  removeAttribute(name){delete this.attributes[name];if(name==='src')this.src='';}
  append(...children){this.children.push(...children);}
  appendChild(child){this.append(child);return child;}
  prepend(child){this.children.unshift(child);}
  after(child){this.afterNode=child;}
  before(child){this.beforeNode=child;}
  querySelector(){return null;}
  load(){this.loadCalls++;this.readyState=this.src?2:0;}
  play(){this.playCalls++;if(this.rejectPlay)return Promise.reject(new Error('blocked'));this.paused=false;return Promise.resolve();}
  pause(){this.paused=true;}
}
async function fixture({reduced=false,preference=null}={}){
 const stage=new Target(),backdrop=new Target(),form=new Target(),win=new Target(),doc=new Target(),media=new Target(),created=[];
 const storage=new Map(preference===null?[]:[['liza-motion',preference]]);
 doc.hidden=false;doc.baseURI='http://localhost:8000/';doc.getElementById=id=>({stage,backdrop,'settings-form':form}[id]||null);doc.createElement=tag=>{const n=new Target(tag);created.push(n);return n;};
 media.matches=reduced;win.matchMedia=()=>media;win.LizaGameState={phase:'play',chapter:0,beat:{speaker:'Luma'}};
 const ctx={window:win,document:doc,location:{origin:'http://localhost:8000'},localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v)},URL,console,fetch:async()=>({ok:true,json:async()=>({version:1,clips:{'luma-pools':{src:'assets/motion/luma-pools.mp4',chapter:0,speakers:['Luma'],loop:true}}})})};
 vm.runInNewContext(source,ctx);
 const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};await flush();
 return {stage,win,doc,media,storage,flush,video:created.find(x=>x.tagName==='video'),checkbox:created.find(x=>x.tagName==='input')};
}
(async()=>{
 const f=await fixture();assert.equal(f.win.QuestMotion.state.visible,true);assert.equal(f.win.QuestMotion.state.readyState,2);assert.equal(f.video.muted,true);assert.equal(f.video.playsInline,true);assert.equal(f.stage.classList.contains('motion-portrait'),true);
 const loadCalls=f.video.loadCalls;
 for(let rev=1;rev<=25;rev++)f.win.emit('game-state',{phase:'play',chapter:0,rev,beat:{speaker:'Luma'}});
 await f.flush();assert.equal(f.video.loadCalls,loadCalls,'unchanged clip cannot reload on game polls');
 f.doc.hidden=true;f.doc.emit('visibilitychange');assert.equal(f.video.paused,true);assert.equal(f.win.QuestMotion.state.visible,false);
 f.doc.hidden=false;f.doc.emit('visibilitychange');await f.flush();assert.equal(f.win.QuestMotion.state.visible,true);
 f.win.emit('game-state',{phase:'play',chapter:0,beat:{speaker:'Pip'}});await f.flush();assert.equal(f.win.QuestMotion.state.clip,null);assert.equal(f.stage.classList.contains('motion-portrait'),false,'different mentor keeps static portrait');
 f.win.emit('game-state',{phase:'play',chapter:0,beat:{speaker:'Luma'}});await f.flush();f.video.emit('error');assert.equal(f.win.QuestMotion.state.visible,false);assert.deepEqual([...f.win.QuestMotion.state.failed],['luma-pools']);
 const failedLoads=f.video.loadCalls;f.win.emit('game-state',{phase:'play',chapter:0,beat:{speaker:'Luma'}});await f.flush();const afterClear=f.video.loadCalls;for(let rev=0;rev<10;rev++)f.win.emit('game-state',{phase:'play',chapter:0,rev,beat:{speaker:'Luma'}});await f.flush();assert.equal(f.video.loadCalls,afterClear,'failed clip cannot repeat network requests');assert.ok(afterClear<=failedLoads+1);
 const r=await fixture({reduced:true});assert.equal(r.win.QuestMotion.state.enabled,false);assert.equal(r.video.loadCalls,0);r.checkbox.checked=true;r.checkbox.emit('change');await r.flush();assert.equal(r.win.QuestMotion.state.visible,true);assert.equal(r.storage.get('liza-motion'),'true');
 const m=await fixture();m.checkbox.checked=false;m.checkbox.emit('change');await m.flush();assert.equal(m.win.QuestMotion.state.visible,false);assert.equal(m.video.paused,true);assert.equal(m.storage.get('liza-motion'),'false');
 const b=await fixture();b.win.emit('game-state',{phase:'map',chapter:0,beat:{speaker:'Luma'}});await b.flush();assert.equal(b.win.QuestMotion.state.clip,null);
 const blocked=await fixture({preference:'false'});blocked.video.rejectPlay=true;blocked.checkbox.checked=true;blocked.checkbox.emit('change');await blocked.flush();assert.equal(blocked.win.QuestMotion.state.visible,false);assert.equal(blocked.video.paused,true);
 console.log('motion lifecycle ok: stable source, decoded visibility, mentor match, hidden-tab pause, scene fallback, failed-source suppression, reduced motion, explicit override, persisted toggle, map teardown, autoplay failure');
})().catch(error=>{console.error(error);process.exitCode=1;});
