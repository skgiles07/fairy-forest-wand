import './vendor/model-viewer.min.js';

// Blender-authored GLBs: actual meshes, materials, and keyframe animation.
// This layer is decorative; sensor rules and the accessible clues stay in game.js.
const encounter = document.getElementById('encounter');
const recipeCenter = document.querySelector('.rune-center');
const mediaPreference = matchMedia('(prefers-reduced-motion: reduce)');
const files = {1:'moon-crystal', 2:'elder-tree', 3:'treasure-chest'};
const model = document.createElement('model-viewer');
model.id = 'landmark-model';
model.setAttribute('aria-hidden', 'true');
model.setAttribute('tabindex', '-1');
model.setAttribute('interaction-prompt', 'none');
model.setAttribute('environment-image', 'neutral');
model.setAttribute('shadow-intensity', '.65');
model.setAttribute('exposure', '1.25');
model.setAttribute('camera-orbit', '25deg 72deg 105%');
model.setAttribute('loading', 'eager');
model.setAttribute('reveal', 'auto');
const state = {station:null, loaded:false, animated:false, failed:[]};
let game = window.LizaGameState || null;

function motionAllowed() {
  return window.QuestMotion?.state.enabled ?? !mediaPreference.matches;
}
function animate() {
  const allowed = motionAllowed() && !document.hidden && !model.hidden && state.loaded;
  if (allowed) model.play();
  else model.pause();
  state.animated = Boolean(allowed && model.availableAnimations?.length);
}
function update() {
  const id = game?.phase === 'play' && game.mode !== 'dialogue' ? game.targets?.[0] : null;
  if (!files[id] || state.failed.includes(id)) {
    model.hidden = true;
    recipeCenter?.classList.remove('has-model');
    animate();
    return;
  }
  const collecting = game.mode === 'collect';
  const parent = collecting ? recipeCenter : encounter;
  if (!parent) return;
  if (model.parentElement !== parent) parent.append(model);
  model.classList.toggle('recipe-model', collecting);
  model.classList.toggle('quest-model', !collecting);
  model.hidden = false;
  if (state.station !== id) {
    state.station = id;
    state.loaded = false;
    state.animated = false;
    recipeCenter?.classList.remove('has-model');
    model.classList.remove('model-ready');
    model.src = `assets/models/${files[id]}.glb`;
  }
  recipeCenter?.classList.toggle('has-model', collecting && state.loaded);
  animate();
}
model.addEventListener('load', () => {
  state.loaded = true;
  model.dataset.animations = (model.availableAnimations || []).join(', ');
  model.classList.add('model-ready');
  update();
});
model.addEventListener('error', () => {
  if (state.station) state.failed.push(state.station);
  state.loaded = false;
  model.classList.remove('model-ready');
  update();
});
window.addEventListener('game-state', event => {game = event.detail; update();});
document.addEventListener('visibilitychange', animate);
document.addEventListener('change', event => {if (event.target.id === 'motion-toggle') animate();});
mediaPreference.addEventListener('change', animate);
window.addEventListener('pagehide', () => model.pause());
window.QuestLandmarks = Object.freeze({
  get state() {return Object.freeze({...state, failed:[...state.failed], animations:[...(model.availableAnimations || [])], visible:!model.hidden && state.loaded});}
});
update();

// Optional browser QA observes the real animation clock, not a mocked timer.
if (new URLSearchParams(location.search).has('verify3d')) {
  setInterval(() => {
    model.dataset.animationTime = String(model.currentTime);
    model.dataset.animationPaused = String(model.paused);
  }, 500);
}
