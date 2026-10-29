'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const params = new URLSearchParams(location.search);
  const defaultStations = [{id:1,name:'Moon Crystal',room:'Choose a room',icon:'◇'},{id:2,name:'Elder Tree',room:'Choose a room',icon:'♧'},{id:3,name:'Treasure Chest',room:'Choose a room',icon:'▣'}];
  let current = null, online = false, busy = false, manual = localStorage.getItem('liza-manual') !== 'false';
  let voice = params.has('voice') || localStorage.getItem('liza-voice') !== 'false';
  let feedbackTimer, lastSpells = new Set(), renderedRev = -1, stations = defaultStations;
  const chapterScenes = ['forest','cave','mountain','pools','fire'];
  const landSymbols = ['✿','◇','❄','♘','♨'];
  const iconFor = name => /dew|water|tear|drop/i.test(name) ? '◈' : /leaf|fern|feather/i.test(name) ? '❧' : /snow|frost|ice/i.test(name) ? '❄' : /bell|chime|song/i.test(name) ? '♪' : /star|sun|spark/i.test(name) ? '✧' : /scale|stone|crystal|gem/i.test(name) ? '◇' : '✦';
  function syncNarrationControls() {
    const state=window.Narration?.state;
    if(!state)return;
    voice=state.enabled;
    $('sound').textContent=voice?'Voice on':'Voice off';
    $('sound').setAttribute('aria-pressed',String(voice));
    $('sound').title=state.status==='blocked'?'Tap to start the story voice':voice?'Mute story voice':'Turn story voice on';
    $('repeat').textContent=!voice?'Hear story':state.status==='blocked' || state.status==='error'?'Tap to hear story':state.status==='playing'?'Replay story':'Hear that again';
    $('repeat').setAttribute('aria-label',state.status==='playing'?'Replay story narration':'Play story narration');
  }
  function syncControls() {
    $('manual-toggle').setAttribute('aria-pressed', String(manual));
    $('manual-toggle').textContent = manual ? 'Preview mode' : 'Wand mode';
    $('sensor-controls').hidden = !manual;
    $('preview-note').textContent = manual ? 'No sensors needed. Click a landmark or press 1, 2, 3.' : 'Use your wand at the three landmarks around the house.';
    syncNarrationControls();
    document.querySelectorAll('.sensor-button').forEach(b => b.disabled = !online || busy || !manual);
    $('continue').disabled = !online || busy;
    ['training-open','training-intro','training-settings-start','training-exit','training-again'].forEach(id=>{if($(id))$(id).disabled=!online || busy;});
  }
  async function request(path, body) {
    const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(path,{method:body === undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal,cache:'no-store'});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'The story keeper could not answer.');
      return data;
    } finally { clearTimeout(timeout); }
  }
  function connection(ok) { online = ok; $('connection').hidden = ok; $('connection').textContent = 'The story keeper is disconnected. Reconnecting…'; syncControls(); }
  function feedback(text, wrong=false) {clearTimeout(feedbackTimer);$('feedback').textContent=text;$('feedback').className='show'+(wrong?' wrong':'');feedbackTimer=setTimeout(()=>$('feedback').className='',3500);}
  function flash(){ $('cast-flash').classList.remove('cast'); void $('cast-flash').offsetWidth; $('cast-flash').classList.add('cast'); }
  async function refresh() {
    const data = await request('/state'), previous = current;
    connection(true); current = data;
    if (data.rev !== renderedRev) {
      render(data); renderedRev = data.rev;
      // One shared effect path for real sensors and preview buttons. Polling the
      // same revision never repeats a cast; room-only edits are not wand hits.
      if (previous && data.rev > previous.rev && Number.isInteger(data.event_station)
          && ['heal','wrong','done'].includes(data.event)
          && JSON.stringify(data.stations_config) === JSON.stringify(previous.stations_config)) {
        if (data.event === 'wrong') feedback(previous.mode === 'dialogue' || previous.phase !== 'play'
          ? 'Come back to the TV. Your friend has something to tell you.'
          : previous.not_yet || 'Try the glowing landmark. Your magic is safe.', true);
        else {
          flash();
          const ingredient = (previous.inventory || []).find(item => item.station === data.event_station);
          const finishedBeat = data.last_step?.beat;
          const foundName = ingredient && !ingredient.collected ? ingredient.name
            : finishedBeat?.mode === 'collect' ? finishedBeat.items_by_station?.[String(data.event_station)] : null;
          feedback(foundName ? foundName + ' found!' : previous.mode === 'boss' || finishedBeat?.mode === 'boss'
            ? 'The shadow is weakening!' : 'Your wand answered!');
        }
      }
    }
    renderTraining(data);
    return data;
  }
  async function action(path, body) {
    if (!online || busy) return null;
    busy = true; syncControls();
    try { const result = await request(path,body); await refresh(); return result; }
    catch (error) { connection(false); feedback(error.message,true); return null; }
    finally { busy=false; syncControls(); }
  }
  async function hit(id, source='preview') {
    window.Narration?.unlock();
    if (!manual || !current || !online || busy) return;
    if (current.phase !== 'play' || current.mode === 'dialogue') { feedback('Come back to the TV. Your friend has something to tell you.'); return; }
    await action('/hit',{station:id,wand_id:source});
  }
  async function startTraining() {
    window.Narration?.unlock();
    if(current?.training){$('settings-open').click();return;}
    const result=await action('/training/start',{});
    if(result){$('settings').close();feedback('Welcome to the Wand Hall. Your adventure will wait.');}
  }
  async function exitTraining() {window.Narration?.unlock();await action('/training/exit',{});$('settings').close();}
  async function practiceAgain() {await action('/reset',{});$('settings').close();}
  async function next() {
    window.Narration?.unlock();
    if(!current || !online || busy)return;
    if(current.training_complete){await exitTraining();return;}
    if(!['intro','map'].includes(current.phase) && current.mode!=='dialogue')return;
    await action('/next',{gen:current.gen});
  }
  function renderTraining(s) {
    const active=Boolean(s.training), diagnostics=s.training_diagnostics || {}, rows=diagnostics.stations || [];
    document.body.dataset.training=String(active);
    $('training-status').hidden=!active;
    $('training-diagnostics').hidden=!active;
    $('training-open').hidden=s.training_available===false && !active;
    $('training-open').textContent=active?'Wand signals':'Wand practice';
    $('training-intro').hidden=active || s.phase!=='intro' || s.training_available===false;
    $('training-settings-start').hidden=active || s.training_available===false;
    $('training-exit').hidden=!active;$('training-again').hidden=!active;
    if(!active)return;
    const wandCount=rows.filter(row=>row.accepted_wand>0).length;
    $('training-runes').innerHTML=stations.map(st=>{
      const row=rows.find(item=>item.id===st.id) || {};
      const source=row.last_source || '';
      const label=source==='wand'?'Wand message':source==='button'?'Station button':source==='preview'?'Preview signal':source?'Other signal':'Waiting';
      return '<div class="training-rune '+esc(source)+'"><span>'+esc(st.icon)+'</span><strong>'+esc(st.name)+'</strong><small>'+label+'</small></div>';
    }).join('');
    $('training-summary').textContent=wandCount?'Wand messages accepted at '+wandCount+' of 3 landmarks.':manual?'Preview practice · physical wand reception still to test.':'Wave at each real landmark. The hub will show its messages here.';
    const ago=row=>row.last_seen_ago_s==null?'No message yet':row.last_seen_ago_s<2?'Just now':Math.round(row.last_seen_ago_s)+'s ago';
    $('training-diagnostic-table').innerHTML='<table><thead><tr><th>Landmark</th><th>Wand</th><th>Button</th><th>Preview</th><th>Last message</th></tr></thead><tbody>'+rows.map(row=>'<tr><th>'+esc(row.name)+'</th><td>'+Number(row.wand || 0)+'</td><td>'+Number(row.button || 0)+'</td><td>'+Number(row.preview || 0)+'</td><td>'+esc(row.last_source || 'waiting')+'<small>'+ago(row)+'</small></td></tr>').join('')+'</tbody></table><p class="training-hardware-note">Hub received '+rows.reduce((sum,row)=>sum+Number(row.total || 0),0)+' messages. Preview and station-button counts stay separate from wand messages. This display does not verify infrared hardware on its own.</p>';
    $('chapter-reset').textContent='Practice again';
    $('campaign-reset').hidden=true;
  }
  function portrait(speaker, chapter) {
    const name = (speaker || '').toLowerCase();
    const index = /black briar/.test(name) ? 5 : /emberwing|dragon/.test(name) ? 4 : /willow|witch/.test(name) ? 3 : /orielle|queen|frost/.test(name) ? 2 : /pip|goblin/.test(name) ? 1 : 0;
    return '<div class="portrait-sprite" style="background-position:'+([0,50,100][index%3])+'% '+(index<3?0:100)+'%"></div>';
  }
  function render(s) {
    stations = s.stations_config?.length ? s.stations_config : stations;
    const training=Boolean(s.training), complete=training && Boolean(s.training_complete);
    const beat = s.beat || {}, play = s.phase==='play', talking=play && s.mode==='dialogue';
    document.body.dataset.phase=s.phase;
    const restored = complete || s.phase === 'finished' || s.phase === 'map';
    $('stage').className='scene-'+(training?'lodge':play?chapterScenes[s.chapter] || s.scene:s.phase==='intro'?'castle':s.phase==='finished'?'forest':'map');
    const progress = restored ? 1 : play ? Math.min(1, (s.progress.done + (s.mode === 'collect' ? (s.items || []).length / Math.max(1, (s.stations || []).length) : 0)) / Math.max(1, s.progress.total - 1)) : .65;
    $('stage').style.setProperty('--restoration', progress.toFixed(3));
    $('backdrop').style.filter = 'saturate(' + (.76 + progress * .43) + ') brightness(' + (.83 + progress * .25) + ')';
    $('stage').classList.toggle('restored', restored);
    $('title').textContent=training?'The Wand Hall':play?s.chapter_title || s.title:s.campaign_title || s.title;
    $('chapter-label').textContent=training?'Great Wolf Lodge · A practice adventure':play?'Chapter '+(s.chapter+1)+' of '+(s.chapters_total||5)+(beat.kind==='hunt'?' · A gathering quest':beat.kind==='encounter'?' · Put your magic to work':''):s.phase==='finished'?'Liza, Keeper of the Heartlight':'Five lands. Three landmarks. One brave Liza.';
    $('speaker').textContent=training?'Luma, your wand guide':play?beat.speaker || s.mentor || 'Your guide':s.phase==='map'?'The realm remembers':s.phase==='finished'?'All your friends':'The Story Keeper';
    $('beat-title').textContent=complete?'Your wand is ready for adventure.':play?beat.title || s.chapter_title:s.phase==='intro'?'Your wand has chosen you.':s.phase==='map'?'A new path is opening.':'The magic was yours all along.';
    $('dialogue').textContent=complete?s.ending:play?(s.dialogue || beat.dialogue || beat.clue || s.clue || s.opening):s.phase==='intro'?s.intro:s.phase==='map'?s.ending:s.ending || 'The Heartlight shines again. Every friend and every land remembers what you did.';
    $('continue').hidden=!(complete || talking || ['intro','map'].includes(s.phase));
    $('continue').textContent=complete?(s.training_return_label || 'Return to your adventure')+' ↵':training && s.progress.done===0?'Receive my wand ↵':s.phase==='intro'?'Begin the adventure ↵':s.phase==='map'?(s.chapter+1 >= (s.chapters_total||5)?'See your happy ending ↵':'Travel to '+(s.next_land || 'the next land')+' ↵'):beat.kind==='forge'?'Learn '+(beat.reward?.spell || 'this spell')+' ↵':beat.kind==='reveal'?'Continue the story ↵':'I’m ready ↵';
    $('step-label').textContent=training?complete?'Practice complete · your adventure is waiting':'Wand practice '+(s.progress.done+1)+' of '+s.progress.total:play?'Quest '+(s.progress.done+1)+' of '+s.progress.total:s.save_error?'Progress could not be saved':s.phase==='intro'?'Start here. Your journey will be saved.':'Your journey is saved.';
    $('mentor-art').innerHTML=training?portrait('Luma',-1):play?portrait(beat.speaker || s.mentor,s.chapter):'';
    const spells=s.spellbook || [];
    $('spells').innerHTML=spells.length?spells.map(sp=>'<div class="spell'+(!lastSpells.has(sp.spell)?' new':'')+'"><span>'+esc(sp.icon || '✧')+'</span>'+esc(sp.spell)+'</div>').join(''):'<p class="empty-spells">Your first spell is waiting to be found.</p>';
    lastSpells=new Set(spells.map(sp=>sp.spell));
    $('journey').hidden=training || !['intro','map'].includes(s.phase);
    const lands=s.lands?.length?s.lands:[{name:'Fairy Pools',chapter:0},{name:'Crystal Caves',chapter:1},{name:'Frozen Mountain',chapter:2},{name:'Unicorn Forest',chapter:3},{name:'Fire Mountain',chapter:4}];
    $('journey').innerHTML=lands.map(l=>'<button type="button" class="landmark '+(l.done?'done':l.next?'next':'locked')+'" '+(!l.next?'disabled':'')+' aria-label="'+esc(l.name)+(l.next?', your next chapter':l.done?', restored':', locked')+'"><span class="land-orb">'+(l.done?'✧':landSymbols[l.chapter] || '✧')+'</span><h2>'+esc(l.name)+'</h2><p>'+(l.done?'Light restored':l.next?'Your next adventure':'A story still to come')+'</p></button>').join('');
    $('journey').querySelector('.next')?.addEventListener('click',next);
    $('chapter-restored').hidden=!complete && !['map','finished'].includes(s.phase);
    $('chapter-restored').querySelector('h2').textContent=complete?'Welcome, young wand keeper.':s.phase==='finished'?'The Heartlight shines again.':(s.chapter_title || 'This land')+' is restored.';
    $('restoration').textContent=complete?'Three landmarks. One wand. Your story is about to begin.':s.phase==='finished'?'Liza, you are the Keeper of the Heartlight.':s.save_error?'Stay here while a grown-up checks the story keeper.':'Take a breath. Your friends will wait until you are ready.';
    $('encounter').hidden=!play || talking || complete;
    $('recipe').hidden=s.mode!=='collect';
    $('recipe-title').textContent=beat.spell || 'Gather the magic'; $('rune-symbol').textContent=iconFor(beat.spell || '');
    $('ingredients').innerHTML=(s.inventory || []).map(item=>{
      const landmark = stations.find(st => st.id === item.station);
      const room = landmark?.room === 'Choose a room' ? 'Landmark ' + item.station : landmark?.room || '';
      return '<div class="ingredient'+(item.collected?' found':'')+'"><span>'+(item.collected?'✓':iconFor(item.name))+'</span>'+esc(item.name)+'<small>'+esc(room)+'</small></div>';
    }).join('');
    $('boss').hidden=s.mode!=='boss'; $('boss-name').textContent=beat.title || 'Break the shadow';
    $('leaves').innerHTML=s.mode==='boss'?Array.from({length:s.hp_max || 0},(_,i)=>'<i class="leaf'+(i<s.hp?'':' spent')+'" aria-hidden="true"></i>').join(''):'';
    $('leaves').setAttribute('aria-label',(s.hp || 0)+' of '+(s.hp_max || 0)+' shadow leaves remaining');
    $('pattern').hidden=s.mode!=='puzzle';
    $('pattern').innerHTML=s.mode==='puzzle'?(s.pattern || []).map((n,i)=>'<span class="'+(i<s.pattern_pos?'complete':i===s.pattern_pos?'next':'')+'" title="'+esc(stations.find(x=>x.id===n)?.name)+'">'+esc(stations.find(x=>x.id===n)?.icon || n)+'</span>').join(''):'';
    $('charge').hidden=s.mode!=='charge'; $('charge-fill').style.width=((s.charge || 0)/(s.charge_max || 1)*100)+'%'; $('charge-label').textContent=(s.charge || 0)+' / '+(s.charge_max || 0)+' waves';
    $('destination').hidden=!play || talking || complete;
    const targets=(s.targets || []).map(id=>stations.find(x=>x.id===id)).filter(Boolean);
    if (targets.length) {
      const destination=targets[0]; $('destination-label').textContent=s.mode==='collect'?'Find '+targets.length+' missing ingredient'+(targets.length===1?'':'s'):beat.spell?'Carry '+beat.spell+' to':'Your next stop';
      $('destination-name').textContent=targets.length>1?'Choose a landmark':destination.name;
      $('destination-room').classList.toggle('room-list', targets.length > 1);
      $('destination-room').innerHTML=targets.length>1?targets.map(st=>'<span>'+esc(st.name)+'<strong>'+esc(st.room==='Choose a room'?'Landmark '+st.id:st.room)+'</strong></span>').join(''):esc(destination.room==='Choose a room'?'Landmark '+destination.id:destination.room);
      $('travel-note').textContent=targets.length>1?'Visit each glowing landmark, then return to the TV.':'Wave your wand here. Then follow the next clue.';
    }
    $('sensor-controls').innerHTML=stations.map(st=>'<button type="button" class="sensor-button'+((s.targets || []).includes(st.id)?' target':'')+((s.items || []).includes(st.id)?' collected':'')+'" data-station="'+st.id+'" aria-label="Wave at '+esc(st.name)+'"><b>'+st.id+'</b>'+esc(st.name)+'</button>').join('');
    $('sensor-controls').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>hit(Number(b.dataset.station))));
    syncControls();
    if (s.save_error) feedback('Your journey could not be saved. Ask a grown-up for help.',true);
    $('chapter-reset').textContent=training?'Practice again':'Replay this chapter';
    $('campaign-reset').hidden=training;
    $('spellbook').hidden=training;
    renderTraining(s);
    const narrationKey=training?(complete?'tutorial:ending':'tutorial:beat:'+s.progress.done):s.phase==='intro'?'intro':s.phase==='finished'?'finished':s.phase==='map'?'chapter:'+s.chapter+':ending':'chapter:'+s.chapter+':beat:'+s.progress.done;
    window.Narration?.present({key:narrationKey,text:$('dialogue').textContent});
    syncNarrationControls();
    window.LizaGameState=s;
    window.dispatchEvent(new CustomEvent('game-state',{detail:s}));
  }
  $('training-open').addEventListener('click',startTraining);
  $('training-intro').addEventListener('click',startTraining);
  $('training-settings-start').addEventListener('click',startTraining);
  $('training-exit').addEventListener('click',exitTraining);
  $('training-again').addEventListener('click',practiceAgain);
  $('continue').addEventListener('click',next);
  $('manual-toggle').addEventListener('click',()=>{manual=!manual;localStorage.setItem('liza-manual',String(manual));syncControls();feedback(manual?'Preview mode: try the landmarks with clicks or keys.':'Wand mode: visit the real landmarks around your house.');});
  $('sound').addEventListener('click',()=>{const state=window.Narration?.state;if(state?.enabled && ['blocked','error','ready'].includes(state.status))window.Narration.replay();else window.Narration?.setEnabled(!state?.enabled);syncNarrationControls();});
  $('repeat').addEventListener('click',()=>{window.Narration?.replay();syncNarrationControls();});
  window.addEventListener('narration-state',syncNarrationControls);
  $('fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{feedback('Use your browser’s full-screen control.');}});
  $('settings-open').addEventListener('click',()=>{$('room-fields').innerHTML=stations.map(st=>'<label>'+esc(st.name)+'<input name="room-'+st.id+'" maxlength="80" placeholder="Which room?" value="'+esc(st.room==='Choose a room'?'':st.room)+'"></label>').join('');$('settings-status').textContent='';$('settings').showModal();});
  $('rooms-save').addEventListener('click',async()=>{const rooms=stations.map(st=>({id:st.id,room:$('settings-form').elements['room-'+st.id].value.trim()}));if(rooms.some(r=>!r.room)){$('settings-status').textContent='Give each landmark a room name.';return;}try{await request('/stations',{stations:rooms});await refresh();$('settings-status').textContent='Room names saved. The house is ready for Liza.';}catch(error){$('settings-status').textContent=error.message;}});
  $('chapter-reset').addEventListener('click',replayChapter);
  $('campaign-reset').addEventListener('click',async()=>{if(!confirm('Start a new adventure? This clears Liza’s saved quest progress.'))return;await action('/reset?campaign=1',{});$('settings').close();});
  async function replayChapter() { if(!online || busy || !confirm(current?.training?'Start wand practice again? Your main adventure stays where you left it.':'Replay this chapter from its beginning?'))return;await action('/reset',{});$('settings').close(); }
  document.addEventListener('keydown',event=>{if(event.repeat || $('settings').open || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName))return;if(event.key==='r'){event.preventDefault();replayChapter();}else if(/^[1-3]$/.test(event.key)){event.preventDefault();hit(Number(event.key),'keyboard');}else if(event.key==='Enter' || event.key==='n' || event.key==='N'){if(event.target.closest('button'))return;event.preventDefault();next();}});
  window.addEventListener('error',event=>{request('/log',{level:'error',msg:String(event.message)}).catch(()=>{});});
  window.addEventListener('unhandledrejection',event=>{request('/log',{level:'error',msg:String(event.reason)}).catch(()=>{});});
  async function poll(){try{await refresh();}catch{connection(false);}setTimeout(poll,500);}
  async function autoplay(){
    let result=document.createElement('output');result.id='autoplay-result';result.hidden=true;document.body.appendChild(result);
    try{
      const visited=new Set(), modes=new Set();
      for(let count=0;count<600;count++){
        const s=await refresh();visited.add(s.chapter);if(s.mode)modes.add(s.mode);
        const stop=params.get('stop_at');
        if(stop && (s.phase===stop || s.chapter_scene===stop || (stop==='frost-queen' && s.chapter===2) || (stop==='good-witch' && s.chapter===3))){result.textContent='pass: visual checkpoint '+stop;await request('/log',{level:'pass',msg:'visual checkpoint '+stop});return;}
        if(s.phase==='finished'){
          if(visited.size!==5)throw new Error('Expected 5 chapters; visited '+visited.size);
          if(!modes.has('dialogue') || !modes.has('collect') || !modes.has('boss'))throw new Error('Missing story, recipe, or encounter coverage');
          if((s.stations_config || []).length!==3)throw new Error('Expected exactly 3 sensors');
          const msg='5 chapters, 3 sensors; dialogue, hunt, forge, puzzle, boss, saved ending verified';result.textContent='pass: '+msg;await request('/log',{level:'pass',msg});return;
        }
        if(s.phase==='intro' || s.phase==='map' || s.mode==='dialogue')await request('/next',{gen:s.gen});
        else {if(!(s.targets || []).length)throw new Error('No target during '+s.mode);const station=s.targets[0];if(![1,2,3].includes(station))throw new Error('Invalid sensor '+station);await request('/hit',{station,wand_id:'autoplay'});}
        await new Promise(resolve=>setTimeout(resolve,40));
      }
      throw new Error('Walkthrough did not finish');
    }catch(error){result.textContent='fail: '+error.message;await request('/log',{level:'fail',msg:error.message});}
  }
  async function autoplayTraining() {
    const result=document.createElement('output');result.id='autoplay-result';result.hidden=true;document.body.appendChild(result);
    try {
      const before=await refresh();
      const checkpoint=JSON.stringify({chapter:before.chapter,phase:before.phase,progress:before.progress,beat:before.beat,spellbook:before.spellbook});
      await startTraining();
      if(!current.training)throw new Error('Wand practice did not start');
      if(!manual){manual=true;syncControls();}
      const modes=new Set();let signals=0;
      for(let index=0;index<100;index++){
        const state=await refresh();
        if(!state.training)throw new Error('Practice left training unexpectedly');
        if(state.training_complete)break;
        modes.add(state.mode);
        if(state.mode==='dialogue')await next();
        else {
          const target=state.targets?.[0];
          if(![1,2,3].includes(target))throw new Error('Practice used an invalid landmark');
          const button=$('sensor-controls').querySelector('[data-station="'+target+'"]');
          if(!button || button.disabled)throw new Error('Preview landmark button unavailable');
          await hit(target,'preview');signals++;
        }
      }
      if(!current.training_complete || $('continue').hidden)throw new Error('Practice completion has no return button');
      const rows=current.training_diagnostics?.stations || [];
      if(rows.length!==3 || rows.reduce((sum,row)=>sum+row.preview,0)!==signals)throw new Error('Preview diagnostics counts differ');
      if(rows.some(row=>row.wand || row.accepted_wand))throw new Error('Preview falsely counted as wand hardware');
      if(!modes.has('charge') || !modes.has('puzzle') || !modes.has('collect'))throw new Error('Practice missed a lesson');
      await next();
      const after=await refresh();
      if(after.training || JSON.stringify({chapter:after.chapter,phase:after.phase,progress:after.progress,beat:after.beat,spellbook:after.spellbook})!==checkpoint)throw new Error('Practice changed suspended adventure');
      const message='Wand Hall UI: 3 preview landmarks, charge, route, hunt, graduation, no false hardware claim, exact adventure resume';
      result.textContent='pass: '+message;await request('/log',{level:'pass',msg:message});
    }catch(error){result.textContent='fail: '+error.message;await request('/log',{level:'fail',msg:error.message});}
  }
  syncControls(); poll(); if(params.get('autoplay')==='training')autoplayTraining();else if(params.has('autoplay'))autoplay();
})();
