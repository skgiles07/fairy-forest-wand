/* Playback-state tests run without audio hardware: node hub/test_narration.js */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
async function test(){
  const saved=new Map(),listeners=new Map(),events=[];
  const audio={src:'',currentTime:0,duration:8,paused:true,plays:0,pauses:0,deny:false,
    addEventListener(type,fn){listeners.set(type,fn);},
    pause(){this.paused=true;this.pauses++;},
    play(){this.plays++;if(this.deny)return Promise.reject(Object.assign(new Error('blocked'),{name:'NotAllowedError'}));this.paused=false;listeners.get('playing')?.();return Promise.resolve();}};
  const window={dispatchEvent(event){events.push(event);}};
  const ctx={window,document:{body:{appendChild(){},dataset:{}},createElement(){return audio;}},location:{search:'',href:'http://localhost:8000/'},URL,URLSearchParams,CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail;}},localStorage:{getItem:key=>saved.get(key)??null,setItem:(key,value)=>saved.set(key,value)},fetch:async()=>({ok:true,json:async()=>({entries:{intro:{text:'Hello Liza.',file:'audio/intro.mp3'},first:{text:'Find the light.',file:'audio/first.mp3'}}})})};
  vm.runInNewContext(fs.readFileSync(__dirname+'/static/narration.js','utf8'),ctx);
  const narration=window.Narration;
  await narration.ready;
  assert.equal(narration.state.enabled,true,'voice defaults on');
  narration.present({key:'intro',text:'Hello Liza.'});
  assert.equal(narration.state.status,'playing');assert.equal(narration.state.source,'local');
  assert.equal(audio.src,'http://localhost:8000/audio/intro.mp3');
  const plays=audio.plays;
  narration.present({key:'intro',text:'Hello Liza.'});assert.equal(audio.plays,plays,'same polling beat does not restart narration');
  narration.present({key:'first',text:'Find the light.'});assert.equal(audio.plays,plays+1);assert.ok(audio.pauses>=2,'prior voice stopped before new beat');
  listeners.get('ended')();assert.equal(narration.state.status,'ended');
  narration.setEnabled(false);assert.equal(narration.state.status,'muted');assert.equal(audio.paused,true);
  const mutedPlays=audio.plays;narration.present({key:'intro',text:'Hello Liza.'});assert.equal(audio.plays,mutedPlays,'muted beat stays silent');
  narration.replay();assert.equal(narration.state.enabled,true);assert.equal(narration.state.status,'playing');
  audio.deny=true;narration.replay();await Promise.resolve();await Promise.resolve();assert.equal(narration.state.status,'blocked','autoplay denial gives actionable state');
  audio.deny=false;narration.unlock();assert.equal(narration.state.status,'playing','user gesture retries blocked current passage');
  assert.ok(events.some(e=>e.type==='narration-state'&&e.detail.status==='playing'));
  assert.ok(events.some(e=>e.type==='narration-state'&&e.detail.status==='ended'));
  console.log('narration tests ok: default voice, local audio, beat dedupe, cancellation, mute, replay, autoplay denial/retry, playback events');
}
test().catch(error=>{console.error(error);process.exitCode=1;});
