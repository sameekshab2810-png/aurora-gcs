const statePill = document.getElementById('state-pill');
const telemetryStatus = document.getElementById('telemetry-status');
const missionState = document.getElementById('mission-state');
const positionReadout = document.getElementById('position-readout');
const waypointReadout = document.getElementById('waypoint-readout');
const progressReadout = document.getElementById('progress-readout');
const baseReadout = document.getElementById('base-readout');
const rateReadout = document.getElementById('rate-readout');
const queueList = document.getElementById('queue-list');
const stackList = document.getElementById('stack-list');
const queueSize = document.getElementById('queue-size');
const stackSize = document.getElementById('stack-size');
const eventLog = document.getElementById('event-log');
const abortBtn = document.getElementById('abort-btn');
const startBtn = document.getElementById('start-btn');
const resetBtn = document.getElementById('reset-btn');
const guidedPanel = document.getElementById('guided-panel');
const welcomePanel = document.getElementById('welcome-panel');
const guidedTitle = document.getElementById('guided-title');
const guidedDescription = document.getElementById('guided-description');
const guidedProgress = document.getElementById('guided-progress');
const continueBtn = document.getElementById('continue-btn');
const backBtn = document.getElementById('back-btn');
const restartDemoBtn = document.getElementById('restart-demo-btn');
const startDemoBtn = document.getElementById('start-demo-btn');
const exploreBtn = document.getElementById('explore-btn');
const canvas = document.getElementById('radar-canvas');
const ctx = canvas.getContext('2d');

const guidedStages = [
  {
    title: '1. The simple idea',
    description: 'The pretend drone starts at home and follows several planned stops. We want to show what the software does if we tell it to stop partway through.'
  },
  {
    title: '2. The two lists',
    description: '“Places still to visit” is the Queue: it works like a to-do list, in order. “Places already reached” is the Stack: it remembers completed stops so the newest one can be used first when returning.'
  },
  {
    title: '3. Start the pretend flight',
    description: 'Click “Start mission”. Watch the red drone move on the map. The green route grows only when the drone reaches a stop; that is when the software saves a checkpoint.'
  },
  {
    title: '4. Trigger the return',
    description: 'After the drone has reached at least one stop, click “Abort mission”. The remaining plan is cancelled, and the drone moves back through its recorded stops, newest stop first, until it reaches home.'
  }
];

const stateDescriptions = {
  IDLE: 'Waiting to start',
  READY: 'Getting ready',
  RUNNING: 'Following the planned route',
  ABORTING: 'Returning through visited stops',
  COMPLETED: 'All planned stops reached',
  SAFE_AT_BASE: 'Back at the starting point'
};

let guideIndex = 0;
let currentState = null;
let pendingRequest = false;

function setGuideStage(index) {
  const stage = guidedStages[index];
  guideIndex = index;
  guidedTitle.textContent = stage.title;
  guidedDescription.textContent = stage.description;
  guidedProgress.style.width = `${((index + 1) / guidedStages.length) * 100}%`;
  backBtn.disabled = index === 0;
  continueBtn.textContent = index === guidedStages.length - 1 ? 'Close guide' : 'Next';
}

function showGuided() {
  welcomePanel.classList.add('hidden');
  guidedPanel.classList.remove('hidden');
  setGuideStage(0);
}

function hideGuided() {
  guidedPanel.classList.add('hidden');
  welcomePanel.classList.remove('hidden');
}

function renderEventList(events) {
  eventLog.innerHTML = '';
  const entries = Array.isArray(events) ? events.slice().reverse() : [];
  entries.forEach((entry) => {
    const item = document.createElement('li');
    const badge = document.createElement('span');
    badge.className = `level-badge level-${entry.level}`;
    badge.textContent = entry.level;
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = `${new Date(entry.timestamp_ms).toLocaleTimeString()} • details`;
    const message = document.createElement('span');
    message.className = 'message';
    message.textContent = entry.message;
    item.appendChild(badge);
    item.appendChild(meta);
    item.appendChild(message);
    eventLog.appendChild(item);
  });
}

function renderQueue(queue) {
  queueList.innerHTML = '';
  queue.forEach((waypoint, index) => {
    const item = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = index === 0 ? 'Next dispatch' : `Waypoint ${index + 1}`;
    const text = document.createElement('span');
    text.textContent = `(${waypoint[0].toFixed(1)}, ${waypoint[1].toFixed(1)})`;
    item.appendChild(strong);
    item.appendChild(document.createTextNode(' '));
    item.appendChild(text);
    queueList.appendChild(item);
  });
  queueSize.textContent = String(queue.length);
}

function renderStack(stack) {
  stackList.innerHTML = '';
  stack.forEach((checkpoint, index) => {
    const item = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = checkpoint.label || `CP ${index + 1}`;
    const text = document.createElement('span');
    text.textContent = `(${checkpoint.x}, ${checkpoint.y}) • seq ${checkpoint.sequence}`;
    item.appendChild(strong);
    item.appendChild(document.createTextNode(' '));
    item.appendChild(text);
    stackList.appendChild(item);
  });
  stackSize.textContent = String(stack.length);
}

function renderState(state) {
  currentState = state;
  const missionStateLabel = state.state || 'IDLE';
  statePill.textContent = missionStateLabel;
  statePill.style.background = missionStateLabel === 'ABORTING' ? 'rgba(255, 97, 109, 0.20)' : missionStateLabel === 'SAFE_AT_BASE' ? 'rgba(113, 239, 178, 0.18)' : 'rgba(105, 215, 255, 0.15)';
  statePill.style.color = missionStateLabel === 'ABORTING' ? '#ffc0c6' : missionStateLabel === 'SAFE_AT_BASE' ? '#aaf7d5' : '#9fe8ff';

  missionState.textContent = stateDescriptions[missionStateLabel] || missionStateLabel;
  positionReadout.textContent = `(${state.coordinates.x.toFixed(1)}, ${state.coordinates.y.toFixed(1)})`;
  waypointReadout.textContent = state.current_waypoint ? `(${state.current_waypoint[0]}, ${state.current_waypoint[1]})` : '—';
  const progressValue = state.mission_progress && state.mission_progress.total_waypoints ? (state.mission_progress.completed / state.mission_progress.total_waypoints) * 100 : 0;
  progressReadout.textContent = `${Math.min(progressValue, 100).toFixed(0)}%`;
  baseReadout.textContent = `(${state.base.x}, ${state.base.y})`;
  rateReadout.textContent = `${state.simulation_rate} Hz`;
  telemetryStatus.textContent = state.simulation_running ? 'Telemetry live' : 'Telemetry idle';
  telemetryStatus.className = `pill ${state.simulation_running ? 'info' : 'muted'}`;
  renderQueue(state.mission_queue || []);
  renderStack(state.rollback_stack || []);
  renderEventList(state.latest_events || []);
  abortBtn.disabled = !state.abort_available;
  startBtn.disabled = state.state !== 'IDLE' || pendingRequest;
  resetBtn.disabled = pendingRequest;
}

async function fetchState() {
  try {
    const response = await fetch('/api/state');
    if (!response.ok) {
      throw new Error('State fetch failed');
    }
    const state = await response.json();
    renderState(state);
  } catch (error) {
    telemetryStatus.textContent = 'Telemetry stale';
    telemetryStatus.className = 'pill muted';
  }
}

async function postAction(url, payload) {
  pendingRequest = true;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || 'Request failed');
    }
    const body = await response.json();
    renderState(body);
    return body;
  } finally {
    pendingRequest = false;
  }
}

function drawRadar(state) {
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const pad = 40;
  const rangeX = 120;
  const rangeY = 80;
  const xScale = (width - pad * 2) / rangeX;
  const yScale = (height - pad * 2) / rangeY;

  ctx.strokeStyle = 'rgba(105, 215, 255, 0.18)';
  ctx.lineWidth = 1;
  for (let x = 0; x <= rangeX; x += 10) {
    const gx = pad + x * xScale;
    ctx.beginPath();
    ctx.moveTo(gx, pad);
    ctx.lineTo(gx, height - pad);
    ctx.stroke();
  }
  for (let y = 0; y <= rangeY; y += 10) {
    const gy = pad + y * yScale;
    ctx.beginPath();
    ctx.moveTo(pad, gy);
    ctx.lineTo(width - pad, gy);
    ctx.stroke();
  }

  const bx = pad + (state.base.x + 60) * xScale;
  const by = height - pad - (state.base.y + 40) * yScale;
  const dx = pad + (state.coordinates.x + 60) * xScale;
  const dy = height - pad - (state.coordinates.y + 40) * yScale;

  ctx.fillStyle = '#69d7ff';
  ctx.beginPath();
  ctx.arc(bx, by, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillText('BASE', bx + 12, by - 10);

  const trajectory = Array.isArray(state.breadcrumbs) ? state.breadcrumbs : [];
  if (trajectory.length > 1) {
    ctx.strokeStyle = '#71efb2';
    ctx.lineWidth = 2;
    ctx.beginPath();
    trajectory.forEach((point, index) => {
      const px = pad + (point.x + 60) * xScale;
      const py = height - pad - (point.y + 40) * yScale;
      if (index === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  if (Array.isArray(state.mission_queue) && state.mission_queue.length) {
    ctx.strokeStyle = '#69d7ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    state.mission_queue.forEach((point, index) => {
      const px = pad + (point[0] + 60) * xScale;
      const py = height - pad - (point[1] + 40) * yScale;
      if (index === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  if (Array.isArray(state.rollback_stack) && state.rollback_stack.length) {
    ctx.strokeStyle = '#f8c249';
    ctx.lineWidth = 2;
    ctx.beginPath();
    state.rollback_stack.forEach((point, index) => {
      const px = pad + (point.x + 60) * xScale;
      const py = height - pad - (point.y + 40) * yScale;
      if (index === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }

  ctx.fillStyle = '#ff616d';
  ctx.beginPath();
  ctx.arc(dx, dy, 7, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillText('DRONE', dx + 12, dy - 8);

  if (state.current_waypoint) {
    const wx = pad + (state.current_waypoint[0] + 60) * xScale;
    const wy = height - pad - (state.current_waypoint[1] + 40) * yScale;
    ctx.strokeStyle = '#69d7ff';
    ctx.beginPath();
    ctx.arc(wx, wy, 10, 0, Math.PI * 2);
    ctx.stroke();
  }
}

function updateDashboard() {
  if (!currentState) return;
  drawRadar(currentState);
}

startBtn.addEventListener('click', async () => {
  try { await postAction('/api/start', {}); } catch (event) { alert(event.message); }
});
abortBtn.addEventListener('click', async () => {
  try { await postAction('/api/abort', { reason: 'Manual emergency abort' }); } catch (event) { alert(event.message); }
});
resetBtn.addEventListener('click', async () => {
  try { await postAction('/api/reset', {}); } catch (event) { alert(event.message); }
});
startDemoBtn.addEventListener('click', showGuided);
exploreBtn.addEventListener('click', hideGuided);
continueBtn.addEventListener('click', () => {
  if (guideIndex < guidedStages.length - 1) {
    setGuideStage(guideIndex + 1);
    return;
  }
  hideGuided();
});
backBtn.addEventListener('click', () => {
  if (guideIndex > 0) setGuideStage(guideIndex - 1);
});
restartDemoBtn.addEventListener('click', () => {
  setGuideStage(0);
  resetBtn.click();
});

setInterval(() => {
  fetchState();
}, 200);

fetchState().then(() => {
  updateDashboard();
});

setInterval(() => {
  updateDashboard();
}, 150);
