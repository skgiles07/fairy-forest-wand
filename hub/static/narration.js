'use strict';
/* Local MP3s are primary. Browser speech is a fallback for new/edited passages.
 * One audio element owns playback so changing a beat never overlaps voices. */
(() => {
  const audio = document.createElement('audio');
  audio.id = 'story-audio'; audio.preload = 'auto'; audio.hidden = true;
  document.body.appendChild(audio);
  const params = new URLSearchParams(location.search);
  let enabled = params.has('voice') || localStorage.getItem('liza-voice') !== 'false';
  let manifest = null, passage = null, generation = 0, unlocked = false, status = 'idle', error = '', source = 'local';
  let voices = [], fallbackSpeech = null;
  const state = () => ({status, enabled, unlocked, key: passage?.key || null, text: passage?.text || '', source, error, currentTime: audio.currentTime, duration: Number.isFinite(audio.duration) ? audio.duration : 0});
  function notify(next, message='') {
    status=next; error=message;
    document.body.dataset.narration=next;
    window.dispatchEvent(new CustomEvent('narration-state',{detail:state()}));
  }
  function stop() {
    generation++; audio.pause();
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    fallbackSpeech=null;
  }
  function loadVoices() { if ('speechSynthesis' in window) voices=speechSynthesis.getVoices(); }
  loadVoices();
  if ('speechSynthesis' in window) speechSynthesis.addEventListener('voiceschanged',loadVoices);
  function speechFallback(token) {
    if (token !== generation || !enabled || !passage) return;
    source='browser';
    if (!('speechSynthesis' in window)) {notify('error','Voice unavailable. Story text remains on screen.');return;}
    if (!unlocked) {notify('blocked','Tap to hear the story.');return;}
    const speech=new SpeechSynthesisUtterance(passage.text); fallbackSpeech=speech;
    speech.lang='en-US'; speech.rate=.88; speech.pitch=1.06;
    speech.voice=voices.find(v=>/Samantha|Karen|Google UK English Female/.test(v.name)) || voices.find(v=>/^en[-_]/.test(v.lang)) || null;
    speech.onstart=()=>{if(token===generation)notify('playing');};
    speech.onend=()=>{if(token===generation){fallbackSpeech=null;notify('ended');}};
    speech.onerror=event=>{if(token===generation && !['canceled','interrupted'].includes(event.error))notify(event.error==='not-allowed'?'blocked':'error','Tap to hear the story.');};
    speechSynthesis.speak(speech);
  }
  function play() {
    if (!enabled || !passage) return;
    stop(); const token=generation;
    if (!manifest) {notify('loading');return;}
    const entry=manifest.entries[passage.key];
    if (!entry || entry.text!==passage.text) {speechFallback(token);return;}
    source='local';
    const url=new URL(entry.file,location.href).href;
    if (audio.src!==url) audio.src=url;
    audio.currentTime=0;
    notify('loading');
    const attempt=audio.play();
    if (attempt && typeof attempt.catch==='function') attempt.catch(reason=>{
      if(token!==generation || !enabled)return;
      if(reason.name==='NotAllowedError')notify('blocked','Tap to hear the story.');
      else if(reason.name!=='AbortError')speechFallback(token);
    });
  }
  audio.addEventListener('playing',()=>{if(enabled){unlocked=true;notify('playing');}});
  audio.addEventListener('ended',()=>{if(enabled)notify('ended');});
  audio.addEventListener('error',()=>{if(enabled && passage)speechFallback(generation);});
  audio.addEventListener('timeupdate',()=>{if(status==='playing')window.dispatchEvent(new CustomEvent('narration-progress',{detail:state()}));});
  const ready=fetch('audio/manifest.json',{cache:'no-cache'}).then(response=>{
    if(!response.ok)throw new Error('Narration files unavailable');return response.json();
  }).then(data=>{manifest=data;if(enabled && passage)play();return data;}).catch(()=>{
    manifest={entries:{}};if(enabled && passage)speechFallback(generation);return manifest;
  });
  window.Narration={
    get state(){return state();}, get ready(){return ready;}, get audio(){return audio;},
    present(next) {
      if(passage?.key===next.key && passage?.text===next.text)return;
      stop();passage={key:next.key,text:next.text};notify(enabled?'ready':'muted');
      if(enabled)play();
    },
    unlock() {unlocked=true;if(enabled && passage && status!=='playing')play();},
    replay() {enabled=true;localStorage.setItem('liza-voice','true');unlocked=true;play();},
    setEnabled(value) {enabled=Boolean(value);localStorage.setItem('liza-voice',String(enabled));stop();notify(enabled?'ready':'muted');if(enabled){unlocked=true;play();}},
    stop() {stop();notify(enabled?'ready':'muted');}
  };
  notify(enabled?'ready':'muted');
})();
