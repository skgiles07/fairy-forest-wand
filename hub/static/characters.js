'use strict';
(() => {
 const cast=[['Luma','luma','A gentle fairy flight'],['Pip','pip','A playful bounding entrance'],['Frost Queen Orielle','queen','A graceful icy glide'],['Good Witch Willow','witch','A magical swirling entrance'],['Emberwing','dragon','A swooping dragon landing'],['Black Briar','briar','A slow creeping reveal']];
 const art=document.getElementById('mentor-art'),nav=document.querySelector('nav');
 let selected=1,bank=null;
 function narrate(){
  const passage=Object.entries(bank?.entries || {}).find(([,p])=>p.role===cast[selected][1]);
  if(passage)window.Narration?.present({key:passage[0],text:passage[1].text});
 }
 function show(index){
  selected=index;
  // Leave/re-enter the preview scene to replay even when selecting the same friend.
  window.dispatchEvent(new CustomEvent('game-state',{detail:{phase:'intro'}}));
  art.innerHTML='<div class="portrait-sprite" style="background-position:'+([0,50,100][index%3])+'% '+(index<3?0:100)+'%"></div>';
  document.getElementById('speaker').textContent=cast[index][0];
  document.getElementById('entrance-description').textContent=cast[index][2]+' · click their name to replay';
  [...nav.children].forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));
  const state={phase:'play',chapter:index,beat:{speaker:cast[index][0]}};
  window.LizaGameState=state;window.dispatchEvent(new CustomEvent('game-state',{detail:state}));
  narrate();
 }
 cast.forEach(([name],index)=>{const button=document.createElement('button');button.type='button';button.textContent=name;button.addEventListener('click',()=>show(index));nav.append(button);});
 document.getElementById('voice-preview').addEventListener('click',()=>{narrate();window.Narration?.replay();});
 window.Narration?.ready.then(data=>{bank=data;narrate();});
 show(selected);
})();
