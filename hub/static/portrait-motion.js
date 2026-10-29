'use strict';
// Animate the existing artwork; no generated model or external media required.
(() => {
  const portrait=document.getElementById('mentor-art');
  if(!portrait)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let sceneKey=null, game=window.LizaGameState || null, entrance=null;
  function enabled(){
    if(window.QuestMotion)return window.QuestMotion.state.enabled;
    const saved=localStorage.getItem('liza-motion');
    return saved===null?!reduced.matches:saved==='true';
  }
  function stop(){entrance?.cancel();entrance=null;portrait.classList.remove('luma-flying','luma-hover');portrait.dataset.flight='still';}
  function update(){
    const speaker=game?.training?'Luma':game?.beat?.speaker || game?.mentor || '';
    const active=game?.phase==='play' && /^luma\b/i.test(speaker);
    const key=active?`${game.training?'tutorial':game.chapter}:${game.phase}:luma`:null;
    if(!active){stop();sceneKey=null;return;}
    if(!enabled() || document.hidden){stop();sceneKey=key;return;}
    portrait.classList.add('luma-hover');
    if(key===sceneKey)return;
    sceneKey=key;
    entrance?.cancel();
    portrait.classList.add('luma-flying');
    if(typeof portrait.animate!=='function'){portrait.classList.remove('luma-flying');return;}
    portrait.dataset.flight='entering';
    portrait.dataset.entrances=String(Number(portrait.dataset.entrances || 0)+1);
    entrance=portrait.animate([
      {transform:'translate(65vw,-18vh) scale(.68) rotate(-16deg)',opacity:0,offset:0},
      {transform:'translate(12vw,-5vh) scale(.93) rotate(-7deg)',opacity:1,offset:.58},
      {transform:'translate(-8px,3px) scale(1.015) rotate(2deg)',opacity:1,offset:.86},
      {transform:'translate(0,0) scale(1) rotate(0deg)',opacity:1,offset:1}
    ],{duration:1250,easing:'cubic-bezier(.2,.65,.25,1)',fill:'none'});
    const current=entrance;
    current.onfinish=()=>{if(entrance===current){entrance=null;portrait.classList.remove('luma-flying');portrait.dataset.flight='hover';}};
  }
  window.addEventListener('game-state',event=>{game=event.detail;update();});
  document.addEventListener('change',event=>{if(event.target.id==='motion-toggle')update();});
  document.addEventListener('visibilitychange',update);
  reduced.addEventListener('change',update);
  window.addEventListener('pagehide',stop);
  window.addEventListener('pageshow',update);
  update();
})();
