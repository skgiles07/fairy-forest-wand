'use strict';
// Distinct entrances for existing character art; no external media or game-state writes.
(() => {
  const portrait=document.getElementById('mentor-art');
  if(!portrait)return;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const pose=(transform,opacity=1,offset)=>({transform,opacity,...(offset===undefined?{}:{offset})});
  const rest=pose('translate(0,0) scale(1) rotate(0deg)',1,1);
  const entrances={
    luma:{duration:1250,frames:[pose('translate(65vw,-18vh) scale(.68) rotate(-16deg)',0,0),pose('translate(12vw,-5vh) scale(.93) rotate(-7deg)',1,.58),pose('translate(-8px,3px) scale(1.015) rotate(2deg)',1,.86),rest]},
    pip:{duration:950,frames:[pose('translate(-38vw,0) scale(.92) rotate(-9deg)',0,0),pose('translate(-28px,-23px) scale(1.03) rotate(5deg)',1,.60),pose('translate(5px,0) scale(.98) rotate(-2deg)',1,.82),rest]},
    queen:{duration:1400,frames:[pose('translate(0,55px) scale(.97)',0,0),pose('translate(0,-5px) scale(1.005)',1,.80),rest]},
    willow:{duration:1150,frames:[pose('translate(-60px,24px) scale(.78) rotate(-13deg)',0,0),pose('translate(10px,-8px) scale(1.02) rotate(3deg)',1,.76),rest]},
    dragon:{duration:1300,frames:[pose('translate(38vw,-13vh) scale(.84) rotate(7deg)',0,0),pose('translate(-3px,9px) scale(1.02,.97) rotate(-1deg)',1,.78),rest]},
    briar:{duration:1600,frames:[pose('translate(-32px,26px) scale(.92)',0,0),pose('translate(-6px,5px) scale(.985)',.78,.72),rest]}
  };
  let sceneKey=null, game=window.LizaGameState || null, entrance=null;
  function character(speaker){
    const name=String(speaker).toLowerCase();
    return /black briar/.test(name)?'briar':/emberwing|dragon/.test(name)?'dragon':/willow|witch/.test(name)?'willow':/orielle|queen|frost/.test(name)?'queen':/pip|goblin/.test(name)?'pip':/^luma\b/.test(name)?'luma':null;
  }
  function enabled(){
    if(window.QuestMotion)return window.QuestMotion.state.enabled;
    const saved=localStorage.getItem('liza-motion');
    return saved===null?!reduced.matches:saved==='true';
  }
  function stop(){
    entrance?.cancel();entrance=null;
    portrait.classList.remove('character-entering','character-idle');
    portrait.dataset.flight='still';
  }
  function fitAboveStory(){
    const stage=document.getElementById('stage'),story=document.querySelector('.story-frame');
    if(!stage || !story)return;
    portrait.style.bottom='';portrait.style.top='';
    const stageBox=stage.getBoundingClientRect(),storyBox=story.getBoundingClientRect();
    const bottom=portrait.offsetTop+portrait.offsetHeight+stageBox.top;
    if(bottom>storyBox.top-24){
      portrait.style.top='auto';
      portrait.style.bottom=(stageBox.bottom-storyBox.top+24)+'px';
    }
  }
  function update(){
    fitAboveStory();
    const who=character(game?.training?'Luma':game?.beat?.speaker || game?.mentor || '');
    const active=game?.phase==='play' && who;
    const key=active?`${game.training?'tutorial':game.chapter}:${game.phase}:${who}`:null;
    if(!active){stop();sceneKey=null;delete portrait.dataset.character;return;}
    portrait.dataset.character=who;
    if(!enabled() || document.hidden){stop();sceneKey=key;return;}
    portrait.classList.add('character-idle');
    if(key===sceneKey)return;
    sceneKey=key;entrance?.cancel();
    if(typeof portrait.animate!=='function')return;
    portrait.classList.add('character-entering');
    portrait.dataset.flight='entering';
    portrait.dataset.entrances=String(Number(portrait.dataset.entrances || 0)+1);
    const effect=entrances[who];
    entrance=portrait.animate(effect.frames,{duration:effect.duration,easing:'cubic-bezier(.2,.65,.25,1)',fill:'none'});
    const current=entrance;
    current.onfinish=()=>{if(entrance===current){entrance=null;portrait.classList.remove('character-entering');portrait.dataset.flight='hover';}};
  }
  window.addEventListener('game-state',event=>{game=event.detail;update();});
  document.addEventListener('change',event=>{if(event.target.id==='motion-toggle')update();});
  document.addEventListener('visibilitychange',update);
  reduced.addEventListener('change',update);
  window.addEventListener('pagehide',stop);
  window.addEventListener('pageshow',update);
  window.addEventListener('resize',fitAboveStory);
  update();
})();
