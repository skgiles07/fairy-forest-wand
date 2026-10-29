'use strict';
(() => {
  const stage = document.getElementById('stage');
  if (!stage) return;
  const preferenceKey = 'liza-motion';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const readPreference = () => {
    try { return localStorage.getItem(preferenceKey); } catch (_) { return null; }
  };
  let savedPreference = readPreference();
  let enabled = savedPreference === null ? !reducedMotion.matches : savedPreference === 'true';
  let gameState = window.LizaGameState || null;
  let clips = [];
  let selected = null;
  let sourceToken = 0;
  let playPending = false;
  let disposed = false;
  const failed = new Set();
  const layer = document.createElement('div');
  layer.id = 'motion-scene';
  layer.setAttribute('aria-hidden', 'true');
  const video = document.createElement('video');
  video.id = 'motion-video';
  video.muted = true;
  video.defaultMuted = true;
  video.playsInline = true;
  video.loop = true;
  video.preload = 'metadata';
  video.tabIndex = -1;
  video.setAttribute('muted', '');
  video.setAttribute('playsinline', '');
  video.setAttribute('disablepictureinpicture', '');
  video.setAttribute('aria-hidden', 'true');
  layer.appendChild(video);
  const backdrop = document.getElementById('backdrop');
  if (backdrop) backdrop.after(layer);
  else stage.prepend(layer);

  const setting = document.createElement('div');
  setting.className = 'motion-preference';
  const settingLabel = document.createElement('label');
  const checkbox = document.createElement('input');
  checkbox.id = 'motion-toggle';
  checkbox.type = 'checkbox';
  checkbox.checked = enabled;
  const caption = document.createElement('span');
  caption.textContent = 'Motion';
  const help = document.createElement('small');
  help.id = 'motion-help';
  help.textContent = 'Turn moving scenes on or off.';
  caption.appendChild(help);
  checkbox.setAttribute('aria-describedby', help.id);
  settingLabel.append(checkbox, caption);
  setting.appendChild(settingLabel);
  const settingsForm = document.getElementById('settings-form');
  const settingsActions = settingsForm?.querySelector('.settings-actions');
  if (settingsActions) settingsActions.before(setting);
  else settingsForm?.appendChild(setting);

  function hide() {
    stage.classList.remove('motion-playing', 'motion-portrait');
  }
  function show() {
    if (!selected || !enabled || document.hidden || video.paused || video.readyState < 2) return;
    stage.classList.add('motion-playing');
    // Hide a static character only when this video depicts that same character.
    const speaker = String(gameState?.beat?.speaker || gameState?.mentor || '').toLowerCase();
    const hasMatchingPortrait = !selected.backgroundOnly
      && (selected.speakers || []).some(name => String(name).toLowerCase() === speaker);
    stage.classList.toggle('motion-portrait', hasMatchingPortrait);
  }
  function fail() {
    if (selected) failed.add(selected.id);
    hide();
    video.pause();
    playPending = false;
  }
  function play() {
    if (!selected || failed.has(selected.id) || !enabled || document.hidden || disposed) return;
    if (!video.paused && video.readyState >= 2) { show(); return; }
    if (playPending) return;
    const token = sourceToken;
    playPending = true;
    let result;
    try { result = video.play(); }
    catch (_) { playPending = false; fail(); return; }
    Promise.resolve(result).then(() => {
      if (token !== sourceToken) return;
      playPending = false;
      if (!enabled || document.hidden) { video.pause(); hide(); return; }
      show();
    }).catch(() => {
      if (token !== sourceToken) return;
      playPending = false;
      fail();
    });
  }
  function choose(state) {
    if (!state || state.phase !== 'play') return null;
    const speaker = String(state.beat?.speaker || state.mentor || '').toLowerCase();
    const candidates = clips.filter(clip => {
      if (failed.has(clip.id) || !(clip.phases || ['play']).includes(state.phase)) return false;
      const exactChapter = Number(clip.chapter) === Number(state.chapter);
      const exactSpeaker = (clip.speakers || []).some(name => String(name).toLowerCase() === speaker);
      return exactChapter && (clip.backgroundOnly || exactSpeaker)
        || exactSpeaker && clip.crossChapter === true;
    });
    return candidates.sort((a, b) => {
      const score = clip => (Number(clip.chapter) === Number(state.chapter) ? 4 : 0)
        + (clip.backgroundOnly ? 0 : 2);
      return score(b) - score(a);
    })[0] || null;
  }
  function update() {
    const next = enabled ? choose(gameState) : null;
    if (!next) {
      hide();
      video.pause();
      if (selected) {
        sourceToken += 1;
        selected = null;
        playPending = false;
        // Clearing an old source aborts its decoder; no invisible video keeps running.
        video.removeAttribute('src');
        video.load();
      }
      return;
    }
    if (selected?.id === next.id) {
      if (document.hidden) { video.pause(); hide(); }
      else play();
      return;
    }
    sourceToken += 1;
    playPending = false;
    hide();
    video.pause();
    selected = next;
    video.loop = next.loop !== false;
    layer.style.setProperty('--motion-position', next.objectPosition || '32% center');
    video.src = next.src;
    video.load();
    play();
  }
  function setEnabled(value) {
    enabled = Boolean(value);
    savedPreference = String(enabled);
    try { localStorage.setItem(preferenceKey, savedPreference); } catch (_) { /* Private browsing can block settings storage. */ }
    checkbox.checked = enabled;
    update();
  }
  checkbox.addEventListener('change', () => setEnabled(checkbox.checked));
  video.addEventListener('playing', show);
  video.addEventListener('loadeddata', () => { if (selected) play(); });
  video.addEventListener('error', fail);
  video.addEventListener('ended', () => { if (!video.loop) hide(); });
  document.addEventListener('visibilitychange', update);
  window.addEventListener('game-state', event => { gameState = event.detail; update(); });
  const onReducedMotion = () => {
    if (savedPreference !== null) return;
    enabled = !reducedMotion.matches;
    checkbox.checked = enabled;
    update();
  };
  if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', onReducedMotion);
  else reducedMotion.addListener?.(onReducedMotion);
  window.addEventListener('pagehide', () => { disposed = true; video.pause(); hide(); });
  window.addEventListener('pageshow', () => { disposed = false; update(); });

  // Read-only diagnostics help validate real decoding without changing game state.
  window.QuestMotion = Object.freeze({
    get state() {
      return Object.freeze({
        enabled, clip: selected?.id || null, playing: !video.paused,
        readyState: video.readyState, visible: stage.classList.contains('motion-playing'),
        failed: [...failed]
      });
    }
  });
  fetch('assets/motion/manifest.json', {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error('Motion manifest unavailable');
      return response.json();
    })
    .then(manifest => {
      if (manifest.version !== 1 || !manifest.clips || typeof manifest.clips !== 'object') return;
      clips = Object.entries(manifest.clips).map(([id, clip]) => {
        if (!clip || typeof clip.src !== 'string') return null;
        const url = new URL(clip.src, document.baseURI);
        if (url.origin !== location.origin || !url.pathname.startsWith('/assets/motion/')) return null;
        return {...clip, id, src: url.href};
      }).filter(Boolean);
      update();
    })
    .catch(() => { hide(); });
})();
