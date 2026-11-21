// Além da Meta Concursos v2.1 - Tactical Operations Engine
// ==================== SECURITY & TOAST UTILITIES (B3 & C3) ====================
function escapeHtml(val) {
  if (val === null || val === undefined) return '';
  return String(val)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function showToast(message, type = 'info', durationMs = 4200) {
  const container = document.getElementById('toast-container');
  if (!container) {
    console.log(`[${type.toUpperCase()}] ${message}`);
    return;
  }
  const msgStr = String(message || '');
  // Auto-detect semantic type when caller uses default 'info'
  let resolved = type;
  if (type === 'info') {
    const low = msgStr.toLowerCase();
    if (low.includes('erro') || low.includes('falha') || low.includes('inválid')) resolved = 'error';
    else if (low.includes('informe') || low.includes('selecione') || low.includes('atenção') || low.includes('nenhum')) resolved = 'warning';
    else if (low.includes('sucesso') || low.includes('êxito') || low.includes('concluíd') || low.includes('qap') || low.includes('salvo') || low.includes('enviado') || low.includes('importado') || low.includes('atualizad') || low.includes('registrad')) resolved = 'success';
  }
  const icons = {
    success: '<i class="fa-solid fa-circle-check text-emerald-400 mt-0.5 shrink-0"></i>',
    error: '<i class="fa-solid fa-circle-xmark text-rose-400 mt-0.5 shrink-0"></i>',
    warning: '<i class="fa-solid fa-triangle-exclamation text-amber-400 mt-0.5 shrink-0"></i>',
    info: '<i class="fa-solid fa-circle-info text-blue-400 mt-0.5 shrink-0"></i>'
  };
  const toast = document.createElement('div');
  toast.className = `tactical-toast toast-${resolved}`;
  toast.innerHTML = `${icons[resolved] || icons.info}<div class="flex-1">${escapeHtml(msgStr).replace(/\n/g, '<br>')}</div><button class="text-slate-500 hover:text-white ml-2 shrink-0" aria-label="Fechar"><i class="fa-solid fa-xmark text-xs"></i></button>`;
  toast.querySelector('button').onclick = () => dismissToast(toast);
  container.appendChild(toast);
  setTimeout(() => dismissToast(toast), durationMs);
}

function dismissToast(toast) {
  if (!toast || toast.dataset.dismissed) return;
  toast.dataset.dismissed = '1';
  toast.classList.add('toast-hiding');
  setTimeout(() => toast.remove(), 260);
}

// State Management
const state = {
  currentTab: 'dashboard',
  currentUser: null,
  profile: null,
  dashboardData: null,
  subjects: [],
  news: [],
  newsFilter: { priority: 'all' },
  revisions: null,
  simulations: [],
  simulationsAnalytics: null,
  dailyPlan: null,
  platforms: [],
  approvals: [],
  tafRecords: [],
  lawData: null,
  errors: [],
  essays: [],
  essayPrompts: [],
  ambientPlaying: false,
  countdownIntervalId: null,
  soundEnabled: true,
  // Timer State
  timer: {
    mode: 'stopwatch', // 'stopwatch' or 'pomodoro'
    running: false,
    intervalId: null,
    seconds: 0,
    pomodoroInitialSeconds: 50 * 60,
    isBreak: false,
    selectedSubjectId: null,
    selectedTopicId: null,
    questionsCorrect: 0,
    questionsIncorrect: 0,
    startTimeStr: null,
    lastTickTimestamp: null
  },
  charts: {
    activityChart: null,
    subjectsChart: null,
    simulationsChart: null
  }
};

// ==================== TACTICAL AUDIO SYNTHESIS (Web Audio API) ====================
class TacticalAudio {
  constructor() {
    this.ctx = null;
    this.ambientNode = null;
    this.ambientGain = null;
    this.ambientType = null;
  }
  
  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  startAmbient(type = 'brown', volume = 0.2) {
    this.stopAmbient();
    this.init();
    if (!this.ctx) return;

    this.ambientGain = this.ctx.createGain();
    this.ambientGain.gain.setValueAtTime(volume, this.ctx.currentTime);
    this.ambientGain.connect(this.ctx.destination);
    this.ambientType = type;

    if (type === 'binaural') {
      // 40Hz Gamma Focus: Carrier 216Hz + 256Hz (differential 40Hz)
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      osc1.type = 'sine';
      osc2.type = 'sine';
      osc1.frequency.setValueAtTime(216, this.ctx.currentTime);
      osc2.frequency.setValueAtTime(256, this.ctx.currentTime);
      
      const g1 = this.ctx.createGain();
      const g2 = this.ctx.createGain();
      g1.gain.value = 0.5;
      g2.gain.value = 0.5;
      
      osc1.connect(g1);
      osc2.connect(g2);
      g1.connect(this.ambientGain);
      g2.connect(this.ambientGain);
      
      osc1.start();
      osc2.start();
      this.ambientNode = { stop: () => { osc1.stop(); osc2.stop(); } };
      return;
    }

    // Noise Generator (Brown / White / Rain)
    const bufferSize = 2 * this.ctx.sampleRate;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      if (type === 'white') {
        output[i] = white * 0.15;
      } else {
        // Brown noise integration
        lastOut = (lastOut + (0.02 * white)) / 1.02;
        output[i] = lastOut * 1.5;
      }
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    if (type === 'rain') {
      const filter = this.ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(1100, this.ctx.currentTime);
      whiteNoise.connect(filter);
      filter.connect(this.ambientGain);
    } else {
      whiteNoise.connect(this.ambientGain);
    }

    whiteNoise.start();
    this.ambientNode = whiteNoise;
  }

  stopAmbient() {
    if (this.ambientNode) {
      try { this.ambientNode.stop(); } catch (e) {}
      this.ambientNode = null;
    }
    this.ambientType = null;
  }

  setAmbientVolume(vol) {
    if (this.ambientGain && this.ctx) {
      this.ambientGain.gain.setValueAtTime(vol, this.ctx.currentTime);
    }
  }

  beep(freq = 880, duration = 0.08, type = 'sine') {
    if (!state.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio error:", e);
    }
  }

  radioChirp() {
    if (!state.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1200, now);
      osc.frequency.exponentialRampToValueAtTime(700, now + 0.12);
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(now + 0.12);
    } catch (e) {}
  }

  missionComplete() {
    if (!state.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const now = this.ctx.currentTime;
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);
        gain.gain.setValueAtTime(0.08, now + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.15);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now + idx * 0.08);
        osc.stop(now + idx * 0.08 + 0.15);
      });
    } catch (e) {}
  }
}

const tacticalSound = new TacticalAudio();

// ==================== INITIALIZATION & MULTI-USER AUTH ====================
// Intercept 401 Unauthorized responses globally to prompt login
const _origFetch = window.fetch.bind(window);
window.fetch = async function(...args) {
  const res = await _origFetch(...args);
  if (res.status === 401 && typeof args[0] === 'string' && !args[0].includes('/api/auth/')) {
    showAuthOverlay('login');
  }
  return res;
};

document.addEventListener('DOMContentLoaded', () => {
  initSidebarState();
  initClock();
  setupNavigation();
  setupTimerUI();
  setupGlobalSearch();
  checkAuthAndBoot();
});

async function checkAuthAndBoot() {
  try {
    const res = await _origFetch('/api/auth/me');
    const data = await res.json();
    if (data && data.authenticated) {
      state.currentUser = data.user || null;
      hideAuthOverlay();
      loadDashboard();
      loadSubjects();
      loadPlatforms();
    } else {
      showAuthOverlay('login');
    }
  } catch (e) {
    console.error('Erro ao verificar sessão:', e);
    showAuthOverlay('login');
  }
}

function showAuthOverlay(tab = 'login') {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) overlay.classList.remove('hidden');
  switchAuthTab(tab);
  onCareerSelectChange();
}

function hideAuthOverlay() {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) overlay.classList.add('hidden');
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById('auth-form-login');
  const regForm = document.getElementById('auth-form-register');
  const btnLogin = document.getElementById('auth-tab-login');
  const btnReg = document.getElementById('auth-tab-register');
  if (!loginForm || !regForm) return;

  if (tab === 'register') {
    loginForm.classList.add('hidden');
    regForm.classList.remove('hidden');
    btnReg.className = 'py-1.5 rounded text-xs font-tactical font-bold bg-slate-100 text-slate-950 transition';
    btnLogin.className = 'py-1.5 rounded text-xs font-tactical font-semibold text-slate-400 hover:text-white transition';
  } else {
    regForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
    btnLogin.className = 'py-1.5 rounded text-xs font-tactical font-bold bg-slate-100 text-slate-950 transition';
    btnReg.className = 'py-1.5 rounded text-xs font-tactical font-semibold text-slate-400 hover:text-white transition';
  }
}

function onCareerSelectChange() {
  const sel = document.getElementById('auth-reg-career');
  const targetInput = document.getElementById('auth-reg-target');
  if (!sel || !targetInput) return;
  const defaults = {
    PM: 'Polícia Militar - Soldado PM',
    PRF: 'Polícia Rodoviária Federal - PRF',
    PF: 'Polícia Federal - Agente',
    PC: 'Polícia Civil - Agente / Investigador',
    PP: 'Polícia Penal - Policial Penal',
    CUSTOM: 'Concurso Público - Alvo Personalizado'
  };
  if (!targetInput.value.trim() || Object.values(defaults).includes(targetInput.value.trim())) {
    targetInput.value = defaults[sel.value] || '';
  }
}

async function submitLogin() {
  const username = document.getElementById('auth-login-user').value.trim();
  const password = document.getElementById('auth-login-pass').value;
  if (!username || !password) {
    showToast('Informe usuário e senha!', 'warning');
    return;
  }
  try {
    const res = await _origFetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Usuário ou senha inválidos.', 'error');
      return;
    }
    state.currentUser = data.user || null;
    hideAuthOverlay();
    tacticalSound.missionComplete();
    showToast(data.message || 'Login realizado com sucesso!', 'success');
    loadDashboard();
    loadSubjects();
    loadPlatforms();
  } catch (e) {
    console.error(e);
    showToast('Erro de conexão ao tentar entrar.', 'error');
  }
}

async function submitRegister() {
  const username = document.getElementById('auth-reg-username').value.trim();
  const display_name = document.getElementById('auth-reg-name').value.trim();
  const email = document.getElementById('auth-reg-email').value.trim();
  const password = document.getElementById('auth-reg-password').value;
  const career_key = document.getElementById('auth-reg-career').value;
  const target_role = document.getElementById('auth-reg-target').value.trim();
  const dailyHours = parseFloat(document.getElementById('auth-reg-daily').value) || 3;

  if (!username || !display_name || password.length < 4) {
    showToast('Preencha usuário, nome e senha (mínimo 4 caracteres).', 'warning');
    return;
  }
  try {
    const res = await _origFetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        display_name,
        email,
        password,
        career_key,
        target_role,
        daily_goal_minutes: Math.round(dailyHours * 60),
        weekly_goal_hours: Math.round(dailyHours * 6)
      })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.detail || 'Não foi possível criar a conta.', 'error');
      return;
    }
    state.currentUser = data.user || null;
    hideAuthOverlay();
    tacticalSound.missionComplete();
    showToast(data.message || 'Conta criada com sucesso!', 'success', 5500);
    loadDashboard();
    loadSubjects();
    loadPlatforms();
  } catch (e) {
    console.error(e);
    showToast('Erro de conexão ao criar conta.', 'error');
  }
}

async function logoutUser() {
  try {
    await _origFetch('/api/auth/logout', { method: 'POST' });
  } catch (e) {}
  state.currentUser = null;
  state.dashboardData = null;
  state.subjects = [];
  showAuthOverlay('login');
  showToast('Sessão encerrada com segurança.', 'info');
}

async function submitChangePassword() {
  const current_password = document.getElementById('modal-pwd-current').value;
  const new_password = document.getElementById('modal-pwd-new').value;
  if (!current_password || new_password.length < 4) {
    showToast('Informe a senha atual e uma nova senha com pelo menos 4 caracteres.', 'warning');
    return;
  }
  try {
    const res = await fetch('/api/auth/password', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password, new_password })
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('modal-pwd-current').value = '';
      document.getElementById('modal-pwd-new').value = '';
      showToast(data.message || 'Senha atualizada!', 'success');
    } else {
      showToast(data.detail || 'Erro ao alterar senha.', 'error');
    }
  } catch (e) {
    showToast('Erro de conexão ao alterar senha.', 'error');
  }
}

async function applyCareerTemplate() {
  const career_key = document.getElementById('modal-profile-career').value;
  const target_role = document.getElementById('modal-profile-target').value.trim();
  try {
    const res = await fetch('/api/career/apply-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ career_key, target_role, mode: 'merge' })
    });
    const data = await res.json();
    if (res.ok) {
      tacticalSound.missionComplete();
      closeModal('modal-profile');
      showToast(data.message || 'Trilha aplicada!', 'success', 5000);
      loadDashboard();
      loadSubjects();
    } else {
      showToast(data.detail || 'Erro ao aplicar trilha.', 'error');
    }
  } catch (e) {
    showToast('Erro de conexão ao aplicar trilha.', 'error');
  }
}

// Live Military Clock & Status
function initClock() {
  const clockEl = document.getElementById('tactical-clock');
  const dateEl = document.getElementById('tactical-date');
  
  function update() {
    const now = new Date();
    if (clockEl) {
      clockEl.innerText = now.toLocaleTimeString('pt-BR', { hour12: false });
    }
    if (dateEl) {
      dateEl.innerText = now.toLocaleDateString('pt-BR', { 
        weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' 
      }).toUpperCase();
    }
  }
  update();
  setInterval(update, 1000);
}

// Tab Navigation
function setupNavigation() {
  const navButtons = document.querySelectorAll('.nav-tab-btn');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
      tacticalSound.beep(1200, 0.04);
    });
  });
}

function switchTab(tabId) {
  if (tabId === 'radar') {
    tabId = 'news';
  }
  state.currentTab = tabId;

  // Map grouped sub-tabs to their sidebar parent button (C4)
  const sidebarAlias = {
    discursivas: 'cadernoerros',
    taf: 'conquistas'
  };
  const activeNavTab = sidebarAlias[tabId] || tabId;
  
  // Highlight navigation button
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === activeNavTab) {
      btn.classList.add('nav-tab-active');
    } else {
      btn.classList.remove('nav-tab-active');
    }
  });

  // Switch visible section
  document.querySelectorAll('.tab-content-panel').forEach(panel => {
    if (panel.id === `tab-${tabId}`) {
      panel.classList.remove('hidden');
    } else {
      panel.classList.add('hidden');
    }
  });

  // Load section-specific data on tab switch
  if (tabId === 'dashboard') loadDashboard();
  else if (tabId === 'subjects') loadSubjects();
  else if (tabId === 'revisions') loadRevisions();
  else if (tabId === 'news') loadNews();
  else if (tabId === 'simulations') loadSimulations();
  else if (tabId === 'arsenal') loadPlatforms();
  else if (tabId === 'conquistas') loadApprovals();
  else if (tabId === 'taf') loadTaf();
  else if (tabId === 'leiseca') loadLawReadings();
  else if (tabId === 'cadernoerros') loadErrors();
  else if (tabId === 'discursivas') { loadEssays(); loadEssayPrompts(); }
  else if (tabId === 'timer') {
    syncTimerDropdowns();
    renderTimerQuickPlatforms();
  }
}

// ==================== DASHBOARD VIEW ====================
async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    state.dashboardData = data;
    state.profile = data.profile;
    state.soundEnabled = data.profile.sound_enabled === 1;
    
    renderDashboardStats(data);
    renderDashboardCharts(data.charts);
    renderRecentSessions(data.recent_sessions);
    renderWeakTopics(data.weak_topics || []);
    loadDailyPlan();
  } catch (err) {
    console.error("Erro ao carregar dashboard:", err);
  }
}

function renderDashboardStats(data) {
  // Rank and Profile
  const rank = data.rank;
  const profile = data.profile;

  document.getElementById('header-user-name').innerText = profile.name || 'Agente Operacional';
  document.getElementById('header-target-role').innerText = profile.target_role || 'Polícia Federal - Agente';
  document.getElementById('badge-rank-title').innerText = rank.title;
  document.getElementById('badge-rank-level').innerText = `NÍVEL ${rank.level}`;
  document.getElementById('rank-xp-hours').innerText = `${rank.total_formatted || (rank.total_hours + 'h')} / ${rank.next_threshold}h`;
  document.getElementById('rank-progress-bar').style.width = `${rank.progress_pct}%`;
  document.getElementById('rank-needed-text').innerText = (rank.needed_seconds > 0 || rank.hours_needed > 0)
    ? `Faltam ${rank.needed_formatted || (rank.hours_needed + 'h')} para a próxima patente` 
    : 'Patente Máxima Atingida!';

  // Today study
  const todayDisplay = data.today.formatted || (data.today.minutes ? `${Math.floor(data.today.minutes / 60)}h ${String(data.today.minutes % 60).padStart(2, '0')}m` : '0h 00m');
  document.getElementById('stat-today-hours').innerText = todayDisplay;
  const todayGoalMins = data.today.goal_minutes || 240;
  const goalH = Math.floor(todayGoalMins / 60);
  const goalM = todayGoalMins % 60;
  const todayGoalFmt = goalM > 0 ? `${goalH}h ${String(goalM).padStart(2, '0')}m` : `${goalH}h 00m`;
  document.getElementById('stat-today-sub').innerText = `Meta: ${todayGoalFmt} (${data.today.progress_pct}% cumprida)`;
  document.getElementById('stat-today-bar').style.width = `${Math.min(100, data.today.progress_pct)}%`;

  // Week study
  const weekDisplay = data.week.formatted || (data.week.hours ? `${data.week.hours}h` : '0h 00m');
  document.getElementById('stat-week-hours').innerText = weekDisplay;
  document.getElementById('stat-week-sub').innerText = `Meta Semanal: ${data.week.goal_hours}h (${data.week.progress_pct}%)`;
  document.getElementById('stat-week-bar').style.width = `${Math.min(100, data.week.progress_pct)}%`;

  // Questions & Precision (Índice de Balística)
  document.getElementById('stat-questions-count').innerText = data.questions.total;
  document.getElementById('stat-questions-accuracy').innerText = `${data.questions.accuracy_pct}%`;
  document.getElementById('stat-questions-sub').innerText = `${data.questions.correct} Acertos / ${data.questions.incorrect} Erros`;
  document.getElementById('stat-questions-bar').style.width = `${data.questions.accuracy_pct}%`;

  // Revisions
  document.getElementById('stat-revisions-count').innerText = data.revisions.total_urgent;
  document.getElementById('stat-revisions-sub').innerText = `${data.revisions.today} hoje • ${data.revisions.overdue} atrasadas`;
  
  if (data.revisions.total_urgent > 0) {
    document.getElementById('revisions-badge-pulse').classList.remove('hidden');
    document.getElementById('stat-revisions-pill').innerText = `${data.revisions.total_urgent} PENDENTES`;
    document.getElementById('stat-revisions-pill').className = 'tactical-pill bg-red-950 text-red-400 border border-red-800 siren-badge';
  } else {
    document.getElementById('revisions-badge-pulse').classList.add('hidden');
    document.getElementById('stat-revisions-pill').innerText = 'EM DIA - QAP';
    document.getElementById('stat-revisions-pill').className = 'tactical-pill bg-emerald-950 text-emerald-400 border border-emerald-800';
  }

  // Countdown HUD (Dia D)
  if (data.countdown) {
    initCountdown(data.countdown);
  }

  // Law reading today stat
  const lawStatEl = document.getElementById('stat-law-count');
  if (lawStatEl) lawStatEl.innerText = data.law_today || 0;

  // Approvals count stat
  const appStatEl = document.getElementById('stat-approvals-count');
  if (appStatEl) appStatEl.innerText = data.approvals_count || 0;

  // Latest TAF pill
  const tafPillEl = document.getElementById('stat-taf-pill');
  if (tafPillEl) {
    if (data.latest_taf) {
      if (data.latest_taf.is_apto) {
        tafPillEl.className = 'tactical-pill bg-emerald-950 text-emerald-400 border border-emerald-800 text-[9px] font-bold inline-block whitespace-nowrap';
        tafPillEl.innerText = 'APTO';
      } else {
        tafPillEl.className = 'tactical-pill bg-rose-950 text-rose-400 border border-rose-800 text-[9px] font-bold inline-block whitespace-nowrap';
        tafPillEl.innerText = 'INAPTO';
      }
    } else {
      tafPillEl.className = 'tactical-pill bg-slate-900 text-slate-400 border border-slate-700 text-[9px] font-bold inline-block whitespace-nowrap';
      tafPillEl.innerText = 'PENDENTE';
    }
  }

  // Streak & Consistency Alert HUD (A3)
  if (data.streak) {
    const st = data.streak;
    const curEl = document.getElementById('streak-current-days');
    const bestEl = document.getElementById('streak-best-days');
    const lastEl = document.getElementById('streak-last-date');
    const msgEl = document.getElementById('streak-alert-msg');
    const bannerEl = document.getElementById('hud-streak-banner');
    const iconBox = document.getElementById('streak-icon-box');

    if (curEl) curEl.innerText = st.current_streak;
    if (bestEl) bestEl.innerText = st.best_streak;
    if (lastEl) lastEl.innerText = st.last_study_date ? `Último plantão: ${st.last_study_date}` : 'Sem plantões registrados';
    if (msgEl) msgEl.innerText = st.alert_message || '';

    if (bannerEl && iconBox) {
      bannerEl.classList.remove('border-emerald-500/40', 'border-amber-500/40', 'border-rose-500/50');
      if (st.alert_level === 'ok') {
        bannerEl.classList.add('border-emerald-500/40');
        iconBox.className = 'w-9 h-9 rounded bg-emerald-950/60 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0';
        if (msgEl) msgEl.className = 'text-[11px] text-emerald-400 mt-0.5 font-medium';
      } else if (st.alert_level === 'warning') {
        bannerEl.classList.add('border-amber-500/40');
        iconBox.className = 'w-9 h-9 rounded bg-amber-950/60 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0';
        if (msgEl) msgEl.className = 'text-[11px] text-amber-300 mt-0.5 font-medium';
      } else {
        bannerEl.classList.add('border-rose-500/50');
        iconBox.className = 'w-9 h-9 rounded bg-rose-950/60 border border-rose-500/40 flex items-center justify-center text-rose-400 shrink-0';
        if (msgEl) msgEl.className = 'text-[11px] text-rose-300 mt-0.5 font-medium';
      }
    }
  }

  // Tactical Cycle (Próxima Missão Ponderada - A1)
  if (data.tactical_cycle) {
    const cycle = data.tactical_cycle;
    const subjEl = document.getElementById('hud-cycle-subject');
    const reasonEl = document.getElementById('hud-cycle-reason');
    const topicEl = document.getElementById('hud-cycle-topic');
    const btnStart = document.getElementById('hud-btn-start-cycle');
    const queueEl = document.getElementById('hud-cycle-queue');

    if (subjEl) subjEl.innerText = cycle.subject_name;
    if (reasonEl) reasonEl.innerText = cycle.reason;
    if (topicEl) {
      topicEl.innerText = cycle.suggested_topic ? `Tópico sugerido: ${cycle.suggested_topic.name}` : 'Estudo Geral do Edital';
    }
    if (btnStart) {
      const topId = cycle.suggested_topic ? cycle.suggested_topic.id : null;
      btnStart.onclick = () => startCycleMission(cycle.subject_id, topId);
    }
    if (queueEl && Array.isArray(cycle.queue)) {
      queueEl.innerHTML = `<span class="text-slate-500 font-mono-tactical mr-1">FILA PONDERADA:</span>` +
        cycle.queue.map((q, idx) => `
          <button onclick="startCycleMission(${q.id}, null)" class="px-2 py-0.5 rounded bg-[#121824] hover:bg-[#1a2234] border border-[#232f46] text-slate-300 flex items-center space-x-1 transition" title="Peso ${q.weight}x • ${q.days_without}d sem estudo">
            <span class="font-mono-tactical text-amber-400 font-bold">#${idx + 1}</span>
            <span>${escapeHtml(q.name)}</span>
            <span class="text-[9px] text-slate-500">(${Number(q.weight).toFixed(1)}x)</span>
          </button>
        `).join('');
    }
  }

  // Active errors & essays count
  const errCountEl = document.getElementById('stat-errors-count');
  if (errCountEl) errCountEl.innerText = data.active_errors_count || 0;

  const essayCountEl = document.getElementById('stat-essays-count');
  if (essayCountEl) essayCountEl.innerText = data.essays_count || 0;
}

// ==================== PLANO DO DIA AUTOMÁTICO (A2) ====================
async function loadDailyPlan(presetMinutes = null) {
  const input = document.getElementById('daily-plan-minutes-input');
  let mins = presetMinutes;
  if (mins !== null && input) {
    input.value = mins;
  } else if (input) {
    mins = parseInt(input.value) || 120;
  } else {
    mins = 120;
  }

  // Highlight active preset button
  document.querySelectorAll('.daily-plan-preset').forEach(btn => {
    const val = parseInt(btn.innerText) * 60;
    if (val === mins) {
      btn.classList.add('border-amber-500/40', 'text-amber-300', 'font-bold');
      btn.classList.remove('border-[#232f44]', 'text-slate-300');
    } else {
      btn.classList.remove('border-amber-500/40', 'text-amber-300', 'font-bold');
      btn.classList.add('border-[#232f44]', 'text-slate-300');
    }
  });

  try {
    const res = await fetch(`/api/daily-plan?minutes=${encodeURIComponent(mins)}`);
    const plan = await res.json();
    state.dailyPlan = plan;
    renderDailyPlan(plan);
  } catch (e) {
    console.error('Erro ao montar plano do dia:', e);
  }
}

function renderDailyPlan(plan) {
  const container = document.getElementById('daily-plan-blocks');
  if (!container) return;
  if (!plan || !plan.blocks || plan.blocks.length === 0) {
    container.innerHTML = `<div class="col-span-2 text-xs text-slate-500 font-mono-tactical p-3 text-center">Cadastre matérias para gerar o plano automático.</div>`;
    return;
  }

  container.innerHTML = plan.blocks.map((b, idx) => `
    <div class="p-3 rounded-lg bg-[#07090e] border border-[#1a2233] hover:border-[#2a3852] transition flex items-center justify-between gap-3">
      <div class="flex items-start space-x-2.5 min-w-0">
        <div class="w-8 h-8 rounded flex items-center justify-center shrink-0 mt-0.5" style="background-color: ${escapeHtml(b.color)}20; border: 1px solid ${escapeHtml(b.color)}55; color: ${escapeHtml(b.color)}">
          <i class="fa-solid ${escapeHtml(b.icon)} text-xs"></i>
        </div>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="text-[9px] font-mono-tactical font-bold px-1.5 py-0.5 rounded bg-[#131a26] text-slate-300 border border-[#232f46]">BLOCO ${idx + 1} • ${b.minutes} min</span>
            <span class="text-[9px] font-mono-tactical text-amber-400 font-bold">${escapeHtml(b.badge)}</span>
          </div>
          <div class="text-xs font-bold text-slate-100 truncate mt-1">${escapeHtml(b.title)}</div>
          <div class="text-[11px] text-slate-400 truncate">${escapeHtml(b.subtitle)}</div>
        </div>
      </div>
      <button onclick="startDailyPlanBlock(${idx})" class="px-2.5 py-1.5 bg-[#151d2c] hover:bg-[#1e2940] text-emerald-400 border border-[#26334a] rounded text-[11px] font-tactical font-bold shrink-0 transition flex items-center space-x-1" title="Executar este bloco agora">
        <i class="fa-solid fa-play text-[9px]"></i>
        <span>INICIAR</span>
      </button>
    </div>
  `).join('');
}

function startDailyPlanBlock(blockIdx) {
  if (!state.dailyPlan || !state.dailyPlan.blocks[blockIdx]) return;
  const b = state.dailyPlan.blocks[blockIdx];
  tacticalSound.radioChirp();
  if (b.type === 'law') {
    switchTab('leiseca');
    showToast(`Bloco de Lei Seca (${b.minutes} min) iniciado!`, 'info');
    return;
  }
  if (b.type === 'revision') {
    switchTab('revisions');
    showToast(`Bloco de Revisão (${b.minutes} min) aberto!`, 'info');
    return;
  }
  if (b.subject_id) {
    startCycleMission(b.subject_id, b.topic_id || null);
    showToast(`Plantão carregado: ${b.title} (${b.minutes} min recomendados).`, 'success');
  } else {
    switchTab('timer');
  }
}

// ==================== MAPA DE FRAQUEZAS POR TÓPICO (A4) ====================
function renderWeakTopics(weakList) {
  const container = document.getElementById('weak-topics-list');
  if (!container) return;

  if (!weakList || weakList.length === 0) {
    container.innerHTML = `
      <div class="md:col-span-2 p-4 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-[#1a2233] rounded">
        <i class="fa-solid fa-shield-check text-emerald-500/70 mr-1.5"></i>
        Nenhum tópico crítico abaixo de 60% de acerto detectado ainda. Registre acertos e erros nos seus plantões para mapear vulnerabilidades!
      </div>`;
    return;
  }

  container.innerHTML = weakList.map(w => `
    <div class="p-2.5 rounded bg-[#07090e] border border-rose-900/40 hover:border-rose-700/60 transition flex items-center justify-between gap-2.5">
      <div class="min-w-0 flex-1">
        <div class="flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full shrink-0" style="background-color: ${escapeHtml(w.subject_color)}"></span>
          <span class="text-[10px] font-mono-tactical text-slate-400 truncate">${escapeHtml(w.subject_name)}</span>
          ${w.active_errors > 0 ? `<span class="text-[9px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-800/60 font-mono-tactical">${w.active_errors} erro(s)</span>` : ''}
        </div>
        <div class="text-xs font-semibold text-slate-100 truncate mt-0.5">${escapeHtml(w.topic_name)}</div>
        <div class="flex items-center space-x-2 mt-1">
          <div class="flex-1 bg-[#111722] h-1.5 rounded-full overflow-hidden">
            <div class="h-full bg-rose-500" style="width: ${Math.min(100, w.accuracy_pct)}%"></div>
          </div>
          <span class="text-[10px] font-mono-tactical font-bold text-rose-400 shrink-0">${w.accuracy_pct}% (${w.questions_correct}A/${w.questions_incorrect}E)</span>
        </div>
      </div>
      <button onclick="scheduleWeakTopicRevision(${w.topic_id})" class="px-2 py-1 bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/60 rounded text-[10px] font-tactical font-bold shrink-0 transition" title="Agendar revisão urgente para hoje">
        <i class="fa-solid fa-rotate mr-1"></i>REVISAR
      </button>
    </div>
  `).join('');
}

async function scheduleWeakTopicRevision(topicId) {
  try {
    const res = await fetch(`/api/weak-topics/${topicId}/schedule-revision`, { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      tacticalSound.beep(1200, 0.06);
      showToast(data.message || 'Tópico enviado para Revisão Urgente!', 'success');
      loadDashboard();
    } else {
      showToast(data.detail || 'Erro ao agendar revisão', 'error');
    }
  } catch (e) {
    console.error(e);
    showToast('Erro de conexão ao agendar revisão.', 'error');
  }
}

function renderDashboardCharts(chartData) {
  // Activity Chart (Last 14 days)
  const ctxActivity = document.getElementById('activityChart');
  if (ctxActivity) {
    if (state.charts.activityChart) state.charts.activityChart.destroy();
    
    state.charts.activityChart = new Chart(ctxActivity, {
      type: 'bar',
      data: {
        labels: chartData.dates,
        datasets: [{
          label: 'Horas Estudadas',
          data: chartData.daily_hours,
          backgroundColor: 'rgba(37, 99, 235, 0.65)',
          borderColor: '#3b82f6',
          borderWidth: 1.5,
          borderRadius: 4,
          hoverBackgroundColor: '#60a5fa'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#3b82f6',
            borderWidth: 1,
            titleColor: '#93c5fd',
            bodyColor: '#f8fafc',
            callbacks: {
              label: (ctx) => {
                const totMins = Math.round((ctx.parsed.y || 0) * 60);
                const h = Math.floor(totMins / 60);
                const m = totMins % 60;
                return ` Tempo: ${h > 0 ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}m`}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(30, 41, 59, 0.4)' },
            ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(30, 41, 59, 0.4)' },
            ticks: { 
              color: '#64748b', 
              font: { family: 'JetBrains Mono', size: 10 },
              callback: (val) => `${val}h`
            }
          }
        }
      }
    });
  }

  // Subject Distribution Chart (Donut)
  const ctxSubjects = document.getElementById('subjectsChart');
  if (ctxSubjects) {
    if (state.charts.subjectsChart) state.charts.subjectsChart.destroy();

    const subData = chartData.subject_distribution;
    const labels = subData.length > 0 ? subData.map(s => s.name) : ['Sem dados ainda'];
    const values = subData.length > 0 ? subData.map(s => s.hours) : [1];
    const colors = subData.length > 0 ? subData.map(s => s.color) : ['#334155'];

    state.charts.subjectsChart = new Chart(ctxSubjects, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: colors,
          borderColor: '#070a12',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#94a3b8',
              font: { family: 'Inter', size: 11 },
              boxWidth: 12,
              padding: 12
            }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            borderColor: '#1e293b',
            borderWidth: 1,
            bodyColor: '#f8fafc',
            callbacks: {
              label: (ctx) => {
                if (!subData || subData.length === 0) return ` ${ctx.label}`;
                const totMins = Math.round((ctx.parsed || 0) * 60);
                const h = Math.floor(totMins / 60);
                const m = totMins % 60;
                return ` ${ctx.label}: ${h > 0 ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}m`}`;
              }
            }
          }
        }
      }
    });
  }
}

function renderRecentSessions(sessions) {
  const container = document.getElementById('recent-sessions-list');
  if (!container) return;

  if (!sessions || sessions.length === 0) {
    container.innerHTML = `
      <div class="p-6 text-center text-slate-500 font-mono-tactical text-xs">
        <i class="fa-solid fa-radar text-slate-600 text-2xl mb-2"></i>
        <p>NENHUM TURNO REGISTRADO AINDA. INICIE SEU PRIMEIRO PLANTÃO DE ESTUDOS!</p>
      </div>`;
    return;
  }

  container.innerHTML = sessions.map(s => `
    <div class="flex items-center justify-between p-3 bg-slate-900/60 rounded border border-slate-800/80 hover:border-slate-700 transition" id="session-row-${s.id}">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded flex items-center justify-center text-white" style="background-color: ${s.subject_color || '#3b82f6'}22; border: 1px solid ${s.subject_color || '#3b82f6'}66">
          <i class="fa-solid ${s.subject_icon || 'fa-book'} text-sm" style="color: ${s.subject_color || '#3b82f6'}"></i>
        </div>
        <div>
          <div class="text-sm font-semibold text-slate-200">${escapeHtml(s.subject_name)}</div>
          <div class="text-xs text-slate-400">${escapeHtml(s.topic_name || 'Estudo Geral da Matéria')}</div>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <div class="text-right">
          <div class="font-mono-tactical text-sm text-blue-400 font-bold">${s.duration_fmt}</div>
          <div class="text-xs text-slate-500">
            ${s.questions_correct + s.questions_incorrect > 0 
              ? `<span class="text-emerald-400">${s.questions_correct}A</span> / <span class="text-rose-400">${s.questions_incorrect}E</span>` 
              : s.date}
          </div>
        </div>
        <div class="flex items-center space-x-1 pl-2 border-l border-slate-800">
          <button onclick="openEditSessionModal(${s.id})" class="text-slate-500 hover:text-blue-400 p-1.5 transition" title="Editar este turno de estudo">
            <i class="fa-solid fa-pencil text-xs"></i>
          </button>
          <button onclick="deleteSession(${s.id})" class="text-slate-600 hover:text-rose-400 p-1.5 transition" title="Excluir este turno">
            <i class="fa-solid fa-trash-can text-xs"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

async function openEditSessionModal(id) {
  try {
    const res = await fetch(`/api/sessions/${id}`);
    if (!res.ok) throw new Error("Erro ao buscar dados do turno");
    const s = await res.json();

    document.getElementById('modal-edit-session-id').value = s.id;

    // Populate subjects
    const subjSelect = document.getElementById('modal-edit-session-subject');
    subjSelect.innerHTML = state.subjects.map(sub => `<option value="${sub.id}" ${sub.id === s.subject_id ? 'selected' : ''}>${sub.name}</option>`).join('');

    // Populate topics for selected subject
    await loadEditSessionTopics(s.topic_id);

    document.getElementById('modal-edit-session-date').value = s.date || '';
    document.getElementById('modal-edit-session-duration').value = Math.round(s.duration_seconds / 60);
    document.getElementById('modal-edit-session-correct').value = s.questions_correct || 0;
    document.getElementById('modal-edit-session-incorrect').value = s.questions_incorrect || 0;
    document.getElementById('modal-edit-session-notes').value = s.notes || '';

    tacticalSound.beep(1100, 0.04);
    document.getElementById('modal-edit-session').classList.remove('hidden');
  } catch (err) {
    showToast("Falha ao abrir turno para edição: " + err.message);
  }
}

async function loadEditSessionTopics(preselectedTopicId = null) {
  const subjId = parseInt(document.getElementById('modal-edit-session-subject').value);
  const topicSelect = document.getElementById('modal-edit-session-topic');
  topicSelect.innerHTML = `<option value="">-- Estudo Geral da Matéria --</option>`;

  const subj = state.subjects.find(s => s.id === subjId);
  if (subj && subj.topics) {
    subj.topics.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      if (preselectedTopicId && t.id === preselectedTopicId) {
        opt.selected = true;
      }
      topicSelect.appendChild(opt);
    });
  }
}

async function submitEditSession() {
  const id = document.getElementById('modal-edit-session-id').value;
  const subjectId = parseInt(document.getElementById('modal-edit-session-subject').value);
  const topicVal = document.getElementById('modal-edit-session-topic').value;
  const topicId = topicVal ? parseInt(topicVal) : null;
  const date = document.getElementById('modal-edit-session-date').value;
  const durationMins = parseInt(document.getElementById('modal-edit-session-duration').value) || 0;
  const correct = parseInt(document.getElementById('modal-edit-session-correct').value) || 0;
  const incorrect = parseInt(document.getElementById('modal-edit-session-incorrect').value) || 0;
  const notes = document.getElementById('modal-edit-session-notes').value.trim();

  if (!subjectId || durationMins <= 0) {
    showToast("Informe a disciplina e uma duração válida em minutos!");
    return;
  }

  try {
    const payload = {
      subject_id: subjectId,
      topic_id: topicId,
      date: date || undefined,
      duration_seconds: durationMins * 60,
      questions_correct: correct,
      questions_incorrect: incorrect,
      notes: notes
    };

    const res = await fetch(`/api/sessions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      tacticalSound.missionComplete();
      closeModal('modal-edit-session');
      loadDashboard();
      loadSubjects();
    } else {
      const err = await res.json();
      showToast("Erro ao atualizar turno: " + (err.detail || "Erro inesperado"));
    }
  } catch (e) {
    console.error(e);
    showToast("Erro na conexão com o servidor");
  }
}

async function deleteSession(id) {
  if (!confirm("Tem certeza que deseja excluir este turno de estudo? As horas e estatísticas serão recalculadas.")) return;
  try {
    const res = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
    if (res.ok) {
      tacticalSound.beep(500, 0.08);
      loadDashboard();
      loadSubjects();
    }
  } catch (err) {
    console.error(err);
  }
}

// ==================== STUDY TIMER & POMODORO ====================
function setupTimerUI() {
  const btnStart = document.getElementById('timer-btn-start');
  const btnPause = document.getElementById('timer-btn-pause');
  const btnReset = document.getElementById('timer-btn-reset');
  const btnSave = document.getElementById('timer-btn-save');
  const modeStopwatch = document.getElementById('timer-mode-stopwatch');
  const modePomodoro = document.getElementById('timer-mode-pomodoro');
  const pomodoroPreset25 = document.getElementById('pomo-preset-25');
  const pomodoroPreset50 = document.getElementById('pomo-preset-50');

  // Mode toggling
  modeStopwatch?.addEventListener('click', () => setTimerMode('stopwatch'));
  modePomodoro?.addEventListener('click', () => setTimerMode('pomodoro'));

  pomodoroPreset25?.addEventListener('click', () => setPomodoroPreset(25));
  pomodoroPreset50?.addEventListener('click', () => setPomodoroPreset(50));

  btnStart?.addEventListener('click', startTimer);
  btnPause?.addEventListener('click', pauseTimer);
  btnReset?.addEventListener('click', resetTimer);
  btnSave?.addEventListener('click', openSaveSessionModal);

  // Question counters
  document.getElementById('btn-add-correct')?.addEventListener('click', () => {
    state.timer.questionsCorrect++;
    tacticalSound.beep(1400, 0.05);
    updateQuestionsLiveUI();
  });

  document.getElementById('btn-add-incorrect')?.addEventListener('click', () => {
    state.timer.questionsIncorrect++;
    tacticalSound.beep(400, 0.08);
    updateQuestionsLiveUI();
  });

  document.getElementById('btn-reset-questions')?.addEventListener('click', () => {
    state.timer.questionsCorrect = 0;
    state.timer.questionsIncorrect = 0;
    updateQuestionsLiveUI();
  });

  // Select subject listener
  document.getElementById('timer-subject-select')?.addEventListener('change', (e) => {
    state.timer.selectedSubjectId = e.target.value ? parseInt(e.target.value) : null;
    populateTimerTopicsDropdown(state.timer.selectedSubjectId);
  });

  document.getElementById('timer-topic-select')?.addEventListener('change', (e) => {
    state.timer.selectedTopicId = e.target.value ? parseInt(e.target.value) : null;
  });

  // Ensure timer syncs immediately when user switches back to this tab
  document.addEventListener('visibilitychange', () => {
    if (state.timer.running) {
      tickTimer();
    }
  });
  window.addEventListener('focus', () => {
    if (state.timer.running) {
      tickTimer();
    }
  });
}

function setTimerMode(mode) {
  if (state.timer.running) {
    if (!confirm("O turno está em andamento. Deseja realmente mudar de modo e reiniciar a contagem?")) return;
    pauseTimer();
  }
  
  state.timer.mode = mode;
  state.timer.isBreak = false;
  state.timer.lastTickTimestamp = null;
  
  const swBtn = document.getElementById('timer-mode-stopwatch');
  const pomoBtn = document.getElementById('timer-mode-pomodoro');
  const pomoPresets = document.getElementById('pomodoro-presets-container');

  if (mode === 'stopwatch') {
    state.timer.seconds = 0;
    swBtn.classList.add('bg-blue-600', 'text-white');
    swBtn.classList.remove('bg-slate-800', 'text-slate-400');
    pomoBtn.classList.remove('bg-blue-600', 'text-white');
    pomoBtn.classList.add('bg-slate-800', 'text-slate-400');
    pomoPresets?.classList.add('hidden');
    document.getElementById('timer-session-label').innerText = 'CRONÔMETRO LIVRE OPERACIONAL';
  } else {
    state.timer.seconds = state.timer.pomodoroInitialSeconds;
    pomoBtn.classList.add('bg-blue-600', 'text-white');
    pomoBtn.classList.remove('bg-slate-800', 'text-slate-400');
    swBtn.classList.remove('bg-blue-600', 'text-white');
    swBtn.classList.add('bg-slate-800', 'text-slate-400');
    pomoPresets?.classList.remove('hidden');
    document.getElementById('timer-session-label').innerText = 'POMODORO TÁTICO: FOCO EM COMBATE';
  }
  
  updateTimerDisplay();
}

function setPomodoroPreset(minutes) {
  if (state.timer.running) pauseTimer();
  state.timer.pomodoroInitialSeconds = minutes * 60;
  state.timer.seconds = state.timer.pomodoroInitialSeconds;
  state.timer.isBreak = false;
  state.timer.lastTickTimestamp = null;
  
  document.getElementById('pomo-preset-25')?.classList.toggle('border-blue-500', minutes === 25);
  document.getElementById('pomo-preset-50')?.classList.toggle('border-blue-500', minutes === 50);
  
  updateTimerDisplay();
}

// ==================== UNTHROTTLED BACKGROUND TIMER (WEB WORKER + WALL-CLOCK DELTA) ====================
let timerWorker = null;

function initTimerWorker() {
  if (timerWorker) return;
  try {
    const workerBlob = new Blob([`
      let interval = null;
      self.onmessage = function(e) {
        if (e.data === 'start') {
          if (interval) clearInterval(interval);
          interval = setInterval(function() {
            self.postMessage('tick');
          }, 500);
        } else if (e.data === 'stop') {
          if (interval) clearInterval(interval);
          interval = null;
        }
      };
    `], { type: 'application/javascript' });
    timerWorker = new Worker(URL.createObjectURL(workerBlob));
    timerWorker.onmessage = function(e) {
      if (e.data === 'tick' && state.timer.running) {
        tickTimer();
      }
    };
  } catch (err) {
    console.warn("Web Worker not supported or restricted, falling back to interval + delta", err);
  }
}

function tickTimer() {
  if (!state.timer.running) return;

  const now = Date.now();
  if (!state.timer.lastTickTimestamp) {
    state.timer.lastTickTimestamp = now;
    return;
  }

  const elapsedMs = now - state.timer.lastTickTimestamp;
  const elapsedSec = Math.floor(elapsedMs / 1000);

  if (elapsedSec >= 1) {
    state.timer.lastTickTimestamp += elapsedSec * 1000;

    if (state.timer.mode === 'stopwatch') {
      state.timer.seconds += elapsedSec;
      updateTimerDisplay();
    } else {
      // Pomodoro countdown
      if (state.timer.seconds > elapsedSec) {
        state.timer.seconds -= elapsedSec;
        updateTimerDisplay();
      } else {
        // Time is up!
        state.timer.seconds = 0;
        updateTimerDisplay();
        handlePomodoroFinished();
      }
    }
  }
}

function startTimer() {
  if (state.timer.running) return;
  tacticalSound.radioChirp();

  // Request browser notification permission for background tab alerts
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }

  if (!state.timer.startTimeStr) {
    const now = new Date();
    state.timer.startTimeStr = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  }

  state.timer.running = true;
  state.timer.lastTickTimestamp = Date.now();

  document.getElementById('timer-btn-start').classList.add('hidden');
  document.getElementById('timer-btn-pause').classList.remove('hidden');
  document.getElementById('timer-radar-status').classList.remove('hidden');

  // Start background Web Worker (unthrottled by browser tabs)
  initTimerWorker();
  if (timerWorker) {
    timerWorker.postMessage('start');
  }

  // Backup interval on main thread
  if (state.timer.intervalId) clearInterval(state.timer.intervalId);
  state.timer.intervalId = setInterval(tickTimer, 500);

  updateTimerDisplay();
}

function pauseTimer() {
  if (!state.timer.running) return;
  tacticalSound.beep(600, 0.05);

  if (state.timer.intervalId) {
    clearInterval(state.timer.intervalId);
    state.timer.intervalId = null;
  }
  if (timerWorker) {
    timerWorker.postMessage('stop');
  }

  // Account for remaining milliseconds
  if (state.timer.lastTickTimestamp) {
    const remainingElapsed = Math.floor((Date.now() - state.timer.lastTickTimestamp) / 1000);
    if (remainingElapsed >= 1) {
      if (state.timer.mode === 'stopwatch') {
        state.timer.seconds += remainingElapsed;
      } else {
        state.timer.seconds = Math.max(0, state.timer.seconds - remainingElapsed);
      }
    }
    state.timer.lastTickTimestamp = null;
  }

  state.timer.running = false;
  document.getElementById('timer-btn-start').classList.remove('hidden');
  document.getElementById('timer-btn-pause').classList.add('hidden');
  document.getElementById('timer-radar-status').classList.add('hidden');

  // Reset tab title
  document.title = "Além da Meta Concursos | Centro de Operações de Estudos Policiais";
  updateTimerDisplay();
}

function resetTimer() {
  if (state.timer.running) pauseTimer();
  if (state.timer.mode === 'stopwatch') {
    state.timer.seconds = 0;
  } else {
    state.timer.seconds = state.timer.pomodoroInitialSeconds;
  }
  state.timer.startTimeStr = null;
  state.timer.lastTickTimestamp = null;
  document.title = "Além da Meta Concursos | Centro de Operações de Estudos Policiais";
  updateTimerDisplay();
}

function handlePomodoroFinished() {
  tacticalSound.missionComplete();
  
  if (state.timer.intervalId) {
    clearInterval(state.timer.intervalId);
    state.timer.intervalId = null;
  }
  if (timerWorker) {
    timerWorker.postMessage('stop');
  }
  state.timer.running = false;
  state.timer.lastTickTimestamp = null;

  if (!state.timer.isBreak) {
    // Focus session finished -> start tactical break
    const msg = "Missão de foco cumprida! Iniciando descanso tático (10 minutos).";
    showTacticalNotification("Missão de Foco Cumprida! QAP!", msg);
    state.timer.isBreak = true;
    state.timer.seconds = 10 * 60;
    const label = document.getElementById('timer-session-label');
    if (label) label.innerText = 'INTERVALO TÁTICO: RECUPERAÇÃO';
    startTimer();
  } else {
    // Break finished -> return to combat focus
    const msg = "Descanso tático concluído! Retornar à posição de combate!";
    showTacticalNotification("Descanso Concluído!", msg);
    state.timer.isBreak = false;
    state.timer.seconds = state.timer.pomodoroInitialSeconds;
    const label = document.getElementById('timer-session-label');
    if (label) label.innerText = 'POMODORO TÁTICO: FOCO EM COMBATE';
    document.getElementById('timer-btn-start').classList.remove('hidden');
    document.getElementById('timer-btn-pause').classList.add('hidden');
    document.getElementById('timer-radar-status').classList.add('hidden');
    document.title = "Além da Meta Concursos | Centro de Operações de Estudos Policiais";
    updateTimerDisplay();
  }
}

function showTacticalNotification(title, body) {
  if ("Notification" in window && Notification.permission === "granted") {
    try {
      new Notification(`🛡️ ${title}`, {
        body: body,
        requireInteraction: true
      });
    } catch (e) {
      console.warn("Notification error:", e);
    }
  }

  // Flash browser tab title to alert the user even in other tabs
  let flashCount = 0;
  const originalTitle = "Além da Meta Concursos | Centro de Operações de Estudos Policiais";
  const flashInterval = setInterval(() => {
    document.title = (flashCount % 2 === 0) ? `🚨 ${title}` : originalTitle;
    flashCount++;
    if (flashCount > 10) {
      clearInterval(flashInterval);
      document.title = originalTitle;
    }
  }, 700);
}

function updateTimerDisplay() {
  const display = document.getElementById('timer-clock-display');
  if (!display) return;
  
  const sec = state.timer.seconds;
  const hours = Math.floor(sec / 3600);
  const minutes = Math.floor((sec % 3600) / 60);
  const seconds = sec % 60;

  const pad = (n) => String(n).padStart(2, '0');
  const timeStr = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  display.innerText = timeStr;

  // Live browser tab title reflection
  if (state.timer.running) {
    const icon = state.timer.isBreak ? '☕' : (state.timer.mode === 'pomodoro' ? '🎯' : '⏱');
    document.title = `${icon} [${timeStr}] Além da Meta Concursos`;
  }
}

function updateQuestionsLiveUI() {
  const correct = state.timer.questionsCorrect;
  const incorrect = state.timer.questionsIncorrect;
  const total = correct + incorrect;
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0;

  document.getElementById('timer-questions-correct').innerText = correct;
  document.getElementById('timer-questions-incorrect').innerText = incorrect;
  document.getElementById('timer-accuracy-display').innerText = `${pct}%`;
}

function syncTimerDropdowns() {
  const subjSelect = document.getElementById('timer-subject-select');
  if (!subjSelect) return;
  
  const currentVal = subjSelect.value;
  subjSelect.innerHTML = `<option value="">-- SELECIONE A DISCIPLINA --</option>` + 
    state.subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    
  if (currentVal) subjSelect.value = currentVal;
  populateTimerTopicsDropdown(subjSelect.value ? parseInt(subjSelect.value) : null);
}

function populateTimerTopicsDropdown(subjectId) {
  const topicSelect = document.getElementById('timer-topic-select');
  if (!topicSelect) return;

  if (!subjectId) {
    topicSelect.innerHTML = `<option value="">-- SELECIONE O TÓPICO (OPCIONAL) --</option>`;
    return;
  }

  const subj = state.subjects.find(s => s.id === subjectId);
  if (!subj || !subj.topics || subj.topics.length === 0) {
    topicSelect.innerHTML = `<option value="">-- NENHUM TÓPICO CADASTRADO --</option>`;
    return;
  }

  topicSelect.innerHTML = `<option value="">-- SELECIONE O TÓPICO (OPCIONAL) --</option>` +
    subj.topics.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
}

function openSaveSessionModal() {
  if (state.timer.running) pauseTimer();
  
  let durationToSave = 0;
  if (state.timer.mode === 'stopwatch') {
    durationToSave = state.timer.seconds;
  } else {
    // Pomodoro elapsed
    durationToSave = Math.max(60, state.timer.pomodoroInitialSeconds - state.timer.seconds);
  }

  if (durationToSave < 60) {
    showToast("Duração de estudo muito curta (mínimo de 1 minuto para registro operacional).");
    return;
  }

  // Pre-fill save modal
  document.getElementById('modal-save-duration').value = Math.round(durationToSave / 60);
  document.getElementById('modal-save-correct').value = state.timer.questionsCorrect;
  document.getElementById('modal-save-incorrect').value = state.timer.questionsIncorrect;
  
  // Open modal
  document.getElementById('modal-save-session').classList.remove('hidden');
}

async function submitSaveSession() {
  const subjSelect = document.getElementById('timer-subject-select');
  const subjectId = subjSelect.value ? parseInt(subjSelect.value) : null;
  
  if (!subjectId) {
    showToast("Selecione qual disciplina você estudou neste turno!");
    return;
  }

  const topicSelect = document.getElementById('timer-topic-select');
  const topicId = topicSelect.value ? parseInt(topicSelect.value) : null;
  
  const minutes = parseInt(document.getElementById('modal-save-duration').value) || 0;
  const correct = parseInt(document.getElementById('modal-save-correct').value) || 0;
  const incorrect = parseInt(document.getElementById('modal-save-incorrect').value) || 0;
  const notes = document.getElementById('modal-save-notes').value || '';
  const autoRevision = document.getElementById('modal-save-autorevision').checked;

  const payload = {
    subject_id: subjectId,
    topic_id: topicId,
    duration_seconds: minutes * 60,
    questions_correct: correct,
    questions_incorrect: incorrect,
    notes: notes,
    auto_create_revision: autoRevision
  };

  try {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      tacticalSound.missionComplete();
      document.getElementById('modal-save-session').classList.add('hidden');
      showToast("Missão Cumprida! Turno de estudo arquivado no seu histórico e revisão de 24h agendada!");
      resetTimer();
      state.timer.questionsCorrect = 0;
      state.timer.questionsIncorrect = 0;
      updateQuestionsLiveUI();
      document.getElementById('modal-save-notes').value = '';
      loadDashboard();
    } else {
      showToast("Erro ao salvar sessão de estudos.");
    }
  } catch (e) {
    console.error(e);
    showToast("Erro na conexão com o servidor.");
  }
}

// Manual study entry modal
function openManualSessionModal() {
  const subjSelect = document.getElementById('manual-modal-subject');
  subjSelect.innerHTML = `<option value="">-- SELECIONE A DISCIPLINA --</option>` +
    state.subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  
  document.getElementById('manual-modal-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-manual-session').classList.remove('hidden');
}

async function submitManualSession() {
  const subjectId = parseInt(document.getElementById('manual-modal-subject').value);
  if (!subjectId) {
    showToast("Selecione a disciplina!");
    return;
  }
  const date = document.getElementById('manual-modal-date').value;
  const hours = parseFloat(document.getElementById('manual-modal-hours').value) || 0;
  const correct = parseInt(document.getElementById('manual-modal-correct').value) || 0;
  const incorrect = parseInt(document.getElementById('manual-modal-incorrect').value) || 0;
  const notes = document.getElementById('manual-modal-notes').value || '';

  if (hours <= 0) {
    showToast("Informe uma quantidade válida de horas!");
    return;
  }

  const payload = {
    subject_id: subjectId,
    date: date,
    duration_seconds: Math.round(hours * 3600),
    questions_correct: correct,
    questions_incorrect: incorrect,
    notes: notes,
    auto_create_revision: true
  };

  try {
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      tacticalSound.missionComplete();
      document.getElementById('modal-manual-session').classList.add('hidden');
      showToast("Turno registrado com sucesso!");
      loadDashboard();
      loadSubjects();
    }
  } catch (err) {
    console.error(err);
  }
}

// ==================== SUBJECTS & TOPICS VIEW ====================
async function loadSubjects() {
  try {
    const res = await fetch('/api/subjects');
    const data = await res.json();
    state.subjects = data;
    renderSubjectsList(data);
    syncTimerDropdowns();
  } catch (err) {
    console.error("Erro ao carregar matérias:", err);
  }
}

function renderSubjectsList(subjects) {
  const container = document.getElementById('subjects-accordion-container');
  if (!container) return;

  if (subjects.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-sm">
        NENHUMA DISCIPLINA CADASTRADA NO EDITAL. CLIQUE EM "+ NOVA DISCIPLINA".
      </div>`;
    return;
  }

  container.innerHTML = subjects.map(s => `
    <div class="tactical-card rounded-lg overflow-hidden mb-4 border border-slate-800" id="subject-card-${s.id}">
      <!-- Subject Header -->
      <div class="p-4 bg-slate-900/80 flex flex-wrap items-center justify-between gap-4 cursor-pointer select-none" onclick="toggleSubjectAccordion(${s.id})">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center text-white" style="background-color: ${escapeHtml(s.color)}22; border: 1px solid ${escapeHtml(s.color)}66">
            <i class="fa-solid ${escapeHtml(s.icon)} text-lg" style="color: ${escapeHtml(s.color)}"></i>
          </div>
          <div>
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="text-base font-bold text-slate-100">${escapeHtml(s.name)}</span>
              <span class="tactical-pill bg-slate-800 text-slate-300 border border-slate-700">${escapeHtml(s.category)}</span>
              <span class="tactical-pill bg-amber-950/60 text-amber-300 border border-amber-500/40 font-mono-tactical text-[9px]" title="Peso no edital (usado no Ciclo Tático e Plano do Dia)">PESO ${Number(s.weight || 1.0).toFixed(1)}x</span>
              ${s.weak_topics_count > 0 ? `<span class="tactical-pill bg-rose-950/80 text-rose-300 border border-rose-700/60 text-[9px] font-bold"><i class="fa-solid fa-triangle-exclamation mr-1"></i>${s.weak_topics_count} FRACO(S)</span>` : ''}
            </div>
            <div class="text-xs text-slate-400 mt-0.5">
              ${s.completed_topics} de ${s.total_topics} tópicos concluídos (${s.progress_pct}%) • Meta: ${s.target_hours || 50}h
            </div>
          </div>
        </div>

        <div class="flex items-center space-x-4 text-right">
          <div>
            <div class="font-mono-tactical text-sm font-bold text-blue-400">${escapeHtml(s.hours_fmt)}</div>
            <div class="text-xs text-slate-500">Horas Estudadas</div>
          </div>
          <div>
            <div class="font-mono-tactical text-sm font-bold ${s.accuracy_pct >= 75 ? 'text-emerald-400' : (s.accuracy_pct >= 50 ? 'text-amber-400' : 'text-rose-400')}">
              ${s.accuracy_pct}%
            </div>
            <div class="text-xs text-slate-500">${s.total_questions} Questões</div>
          </div>
          <button onclick="event.stopPropagation(); openEditSubjectModal(${s.id})" class="text-slate-400 hover:text-amber-300 p-1.5 rounded hover:bg-slate-800 transition" title="Ajustar peso no edital e meta da matéria">
            <i class="fa-solid fa-sliders text-xs"></i>
          </button>
          <i class="fa-solid fa-chevron-down text-slate-500 transition-transform duration-200" id="accordion-arrow-${s.id}"></i>
        </div>
      </div>

      <!-- Progress bar -->
      <div class="w-full bg-slate-950 h-1.5">
        <div class="h-1.5 transition-all duration-300" style="width: ${s.progress_pct}%; background-color: ${escapeHtml(s.color)}"></div>
      </div>

      <!-- Topics Content (Collapsible) -->
      <div class="hidden bg-slate-950/60 p-4 border-t border-slate-800/80" id="subject-topics-${s.id}">
        <div class="flex items-center justify-between mb-3">
          <div class="text-xs font-tactical text-slate-400 tracking-wider">TÓPICOS DO EDITAL ESQUEMATIZADO</div>
          <button onclick="openAddTopicModal(${s.id}, '${escapeHtml(s.name).replace(/'/g, "\\'")}')" class="text-xs bg-slate-800 hover:bg-slate-700 text-blue-400 px-2.5 py-1 rounded border border-slate-700 flex items-center space-x-1">
            <i class="fa-solid fa-plus text-xs"></i>
            <span>Adicionar Tópico</span>
          </button>
        </div>

        <div class="space-y-2">
          ${s.topics.map(t => `
            <div class="flex flex-wrap items-center justify-between p-2.5 rounded border transition ${t.is_weak ? 'bg-rose-950/20 border-rose-800/60 hover:border-rose-600/70' : 'bg-slate-900/50 border-slate-800/60 hover:border-slate-700'}" id="topic-item-${t.id}">
              <div class="text-sm text-slate-300 flex-1 pr-4">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="font-medium ${t.is_weak ? 'text-rose-200' : ''}">${escapeHtml(t.name)}</span>
                  ${t.total_questions > 0 ? `<span class="text-[10px] font-mono-tactical px-1.5 py-0.5 rounded border ${t.accuracy_pct < 60 ? 'bg-rose-950 text-rose-300 border-rose-700 font-bold' : (t.accuracy_pct < 75 ? 'bg-amber-950 text-amber-300 border-amber-700' : 'bg-emerald-950 text-emerald-300 border-emerald-700')}">${t.accuracy_pct}% (${t.questions_correct}A/${t.questions_incorrect}E)</span>` : ''}
                  ${t.active_errors > 0 ? `<span class="text-[10px] font-mono-tactical px-1.5 py-0.5 rounded bg-rose-950/70 text-rose-300 border border-rose-800/60">${t.active_errors} erro(s)</span>` : ''}
                </div>
                ${t.notes ? `<div class="text-[11px] text-slate-500 italic mt-0.5">${escapeHtml(t.notes)}</div>` : ''}
              </div>
              <div class="flex items-center space-x-1.5 mt-1 sm:mt-0">
                ${t.is_weak ? `<button onclick="scheduleWeakTopicRevision(${t.id})" class="px-2 py-0.5 rounded text-[11px] border bg-rose-950 hover:bg-rose-900 text-rose-200 border-rose-700 font-tactical font-bold transition" title="Enviar tópico fraco para revisão hoje"><i class="fa-solid fa-rotate mr-1"></i>Revisar</button>` : ''}
                <!-- Checkbox Teoria -->
                <button onclick="toggleTopicCheck(${t.id}, 'theory_completed')" class="px-2 py-0.5 rounded text-xs border font-mono-tactical transition ${t.theory_completed ? 'bg-emerald-950 text-emerald-300 border-emerald-700' : 'bg-slate-800 text-slate-500 border-slate-700'}">
                  ${t.theory_completed ? '✓ Teoria' : 'Teoria'}
                </button>
                <!-- Checkbox Resumo -->
                <button onclick="toggleTopicCheck(${t.id}, 'summary_completed')" class="px-2 py-0.5 rounded text-xs border font-mono-tactical transition ${t.summary_completed ? 'bg-emerald-950 text-emerald-300 border-emerald-700' : 'bg-slate-800 text-slate-500 border-slate-700'}">
                  ${t.summary_completed ? '✓ Resumo' : 'Resumo'}
                </button>
                <!-- Checkbox Questões -->
                <button onclick="toggleTopicCheck(${t.id}, 'questions_completed')" class="px-2 py-0.5 rounded text-xs border font-mono-tactical transition ${t.questions_completed ? 'bg-emerald-950 text-emerald-300 border-emerald-700' : 'bg-slate-800 text-slate-500 border-slate-700'}">
                  ${t.questions_completed ? '✓ Questões' : 'Questões'}
                </button>
                <!-- Edit topic -->
                <button onclick="openEditTopicModal(${t.id})" class="text-slate-500 hover:text-blue-400 p-1 transition" title="Editar tópico e notas">
                  <i class="fa-solid fa-pencil text-xs"></i>
                </button>
                <!-- Delete topic -->
                <button onclick="deleteTopic(${t.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir tópico">
                  <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

function toggleSubjectAccordion(id) {
  const panel = document.getElementById(`subject-topics-${id}`);
  const arrow = document.getElementById(`accordion-arrow-${id}`);
  if (!panel) return;
  
  tacticalSound.beep(900, 0.03);
  const isHidden = panel.classList.contains('hidden');
  panel.classList.toggle('hidden');
  arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
}

async function toggleTopicCheck(topicId, field) {
  try {
    tacticalSound.beep(1300, 0.04);
    const res = await fetch(`/api/topics/${topicId}/toggle?field=${field}`, { method: 'PUT' });
    if (res.ok) {
      loadSubjects();
      loadDashboard();
    }
  } catch (err) {
    console.error(err);
  }
}

async function deleteTopic(topicId) {
  if (!confirm("Deseja excluir este tópico?")) return;
  try {
    await fetch(`/api/topics/${topicId}`, { method: 'DELETE' });
    loadSubjects();
  } catch (e) {
    console.error(e);
  }
}

function openAddTopicModal(subjectId, subjectName) {
  document.getElementById('modal-add-topic-subj-id').value = subjectId;
  document.getElementById('modal-add-topic-subj-name').innerText = subjectName;
  document.getElementById('modal-add-topic-name').value = '';
  document.getElementById('modal-add-topic').classList.remove('hidden');
}

async function submitAddTopic() {
  const subjectId = document.getElementById('modal-add-topic-subj-id').value;
  const name = document.getElementById('modal-add-topic-name').value.trim();
  if (!name) return;

  try {
    await fetch(`/api/subjects/${subjectId}/topics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name })
    });
    document.getElementById('modal-add-topic').classList.add('hidden');
    tacticalSound.beep(1200, 0.05);
    loadSubjects();
  } catch (e) {
    console.error(e);
  }
}

async function openEditTopicModal(topicId) {
  try {
    const res = await fetch(`/api/topics/${topicId}`);
    if (!res.ok) throw new Error("Erro ao buscar dados do tópico");
    const t = await res.json();

    document.getElementById('modal-edit-topic-id').value = t.id;
    document.getElementById('modal-edit-topic-name').value = t.name || '';
    document.getElementById('modal-edit-topic-notes').value = t.notes || '';

    tacticalSound.beep(1100, 0.04);
    document.getElementById('modal-edit-topic').classList.remove('hidden');
  } catch (err) {
    showToast("Falha ao abrir tópico para edição: " + err.message);
  }
}

async function submitEditTopic() {
  const id = document.getElementById('modal-edit-topic-id').value;
  const name = document.getElementById('modal-edit-topic-name').value.trim();
  const notes = document.getElementById('modal-edit-topic-notes').value.trim();

  if (!name) {
    showToast("Informe o nome do tópico!");
    return;
  }

  try {
    const res = await fetch(`/api/topics/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, notes: notes })
    });

    if (res.ok) {
      tacticalSound.missionComplete();
      closeModal('modal-edit-topic');
      loadSubjects();
    } else {
      const err = await res.json();
      showToast("Erro ao atualizar tópico: " + (err.detail || "Erro inesperado"));
    }
  } catch (e) {
    console.error(e);
    showToast("Erro na conexão com o servidor");
  }
}

function openAddSubjectModal() {
  document.getElementById('modal-add-subject').classList.remove('hidden');
}

async function submitAddSubject() {
  const name = document.getElementById('modal-subj-name').value.trim();
  const category = document.getElementById('modal-subj-category').value;
  const color = document.getElementById('modal-subj-color').value;
  const target = parseFloat(document.getElementById('modal-subj-target').value) || 50;
  const weightEl = document.getElementById('modal-subj-weight');
  const weight = weightEl ? (parseFloat(weightEl.value) || 2.0) : 2.0;

  if (!name) {
    showToast("Informe o nome da disciplina!", "warning");
    return;
  }

  try {
    await fetch('/api/subjects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        category: category,
        color: color,
        target_hours: target,
        weight: weight
      })
    });
    document.getElementById('modal-add-subject').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(`Disciplina "${name}" (peso ${weight.toFixed(1)}x) cadastrada!`, "success");
    loadSubjects();
    loadDashboard();
  } catch (e) {
    console.error(e);
    showToast("Erro ao cadastrar disciplina.", "error");
  }
}

// ==================== EDITAR DISCIPLINA & PESO DO EDITAL (A1) ====================
function openEditSubjectModal(subjectId) {
  const s = state.subjects.find(x => x.id === subjectId);
  if (!s) return;
  document.getElementById('modal-edit-subj-id').value = s.id;
  document.getElementById('modal-edit-subj-name').value = s.name || '';
  document.getElementById('modal-edit-subj-category').value = s.category || 'Jurídica';
  document.getElementById('modal-edit-subj-target').value = s.target_hours || 50;
  document.getElementById('modal-edit-subj-weight').value = s.weight || 1.0;
  tacticalSound.beep(1100, 0.04);
  document.getElementById('modal-edit-subject').classList.remove('hidden');
}

async function submitEditSubject() {
  const id = document.getElementById('modal-edit-subj-id').value;
  const name = document.getElementById('modal-edit-subj-name').value.trim();
  const category = document.getElementById('modal-edit-subj-category').value;
  const target = parseFloat(document.getElementById('modal-edit-subj-target').value) || 50;
  const weight = parseFloat(document.getElementById('modal-edit-subj-weight').value) || 1.0;

  if (!name) {
    showToast("Informe o nome da disciplina!", "warning");
    return;
  }
  try {
    const res = await fetch(`/api/subjects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, category, target_hours: target, weight })
    });
    if (res.ok) {
      closeModal('modal-edit-subject');
      tacticalSound.missionComplete();
      showToast(`Disciplina atualizada (Peso ${weight.toFixed(1)}x)! Ciclo e Plano recalculados.`, "success");
      loadSubjects();
      loadDashboard();
    } else {
      const err = await res.json();
      showToast(err.detail || "Erro ao atualizar disciplina.", "error");
    }
  } catch (e) {
    console.error(e);
    showToast("Erro de conexão ao atualizar disciplina.", "error");
  }
}

// ==================== IMPORTADOR DE EDITAL VERTICALIZADO (A5) ====================
function openImportEditalModal() {
  document.getElementById('modal-edital-text').value = '';
  const box = document.getElementById('edital-preview-box');
  if (box) {
    box.innerHTML = '';
    box.classList.add('hidden');
  }
  tacticalSound.beep(1100, 0.04);
  document.getElementById('modal-import-edital').classList.remove('hidden');
}

async function previewEditalImport() {
  const text = document.getElementById('modal-edital-text').value.trim();
  const mode = document.getElementById('modal-edital-mode').value;
  const box = document.getElementById('edital-preview-box');
  if (!text) {
    showToast("Cole o texto do conteúdo programático antes de pré-visualizar.", "warning");
    return;
  }
  try {
    const res = await fetch('/api/edital/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, mode })
    });
    const data = await res.json();
    box.classList.remove('hidden');
    if (!data.subjects || data.subjects.length === 0) {
      box.innerHTML = `<div class="text-rose-400">Nenhuma matéria reconhecida. Coloque cada matéria em MAIÚSCULAS ou com "MATÉRIA: Nome".</div>`;
      return;
    }
    box.innerHTML = `
      <div class="text-amber-300 font-tactical font-bold mb-2">
        PRÉVIA: ${data.subjects_count} matéria(s) e ${data.topics_count} tópico(s) identificados
      </div>
      ${data.subjects.map(s => `
        <div class="p-2 rounded bg-[#0c1017] border border-[#182030]">
          <div class="flex flex-wrap items-center gap-1.5">
            <span class="font-bold text-slate-100">${escapeHtml(s.name)}</span>
            <span class="text-[10px] font-mono-tactical text-amber-300">Peso ${Number(s.weight).toFixed(1)}x</span>
            ${s.matched_existing
              ? `<span class="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">Preserva horas de: ${escapeHtml(s.matched_existing)}</span>`
              : `<span class="text-[10px] px-1.5 py-0.2 rounded bg-blue-950 text-blue-300 border border-blue-700">Nova matéria</span>`}
          </div>
          <div class="text-[11px] text-slate-400 mt-1">${s.topics.length} tópico(s): ${escapeHtml(s.topics.slice(0, 4).join(' • '))}${s.topics.length > 4 ? ' ...' : ''}</div>
        </div>
      `).join('')}
    `;
  } catch (e) {
    console.error(e);
    showToast("Erro ao pré-visualizar edital.", "error");
  }
}

async function submitEditalImport() {
  const text = document.getElementById('modal-edital-text').value.trim();
  const mode = document.getElementById('modal-edital-mode').value;
  if (!text) {
    showToast("Cole o conteúdo programático do edital!", "warning");
    return;
  }
  try {
    const res = await fetch('/api/edital/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, mode })
    });
    const data = await res.json();
    if (res.ok) {
      closeModal('modal-import-edital');
      tacticalSound.missionComplete();
      showToast(data.message || "Edital importado com sucesso!", "success", 5500);
      loadSubjects();
      loadDashboard();
    } else {
      showToast(data.detail || "Falha ao importar edital.", "error");
    }
  } catch (e) {
    console.error(e);
    showToast("Erro de conexão ao importar edital.", "error");
  }
}

// ==================== REVISIONS (SPACED REPETITION) ====================
async function loadRevisions() {
  try {
    const res = await fetch('/api/revisions');
    const data = await res.json();
    state.revisions = data;
    renderRevisions(data);
  } catch (err) {
    console.error("Erro ao carregar revisões:", err);
  }
}

function renderRevisions(data) {
  const todayContainer = document.getElementById('revisions-today-list');
  const overdueContainer = document.getElementById('revisions-overdue-list');
  const upcomingContainer = document.getElementById('revisions-upcoming-list');
  const completedContainer = document.getElementById('revisions-completed-list');

  // Today
  if (todayContainer) {
    if (data.today.length === 0) {
      todayContainer.innerHTML = `
        <div class="p-6 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded">
          NENHUMA REVISÃO PROGRAMADA PARA HOJE. VOCÊ ESTÁ QAP TOTAL!
        </div>`;
    } else {
      todayContainer.innerHTML = data.today.map(r => renderRevisionCard(r, 'today')).join('');
    }
  }

  // Overdue
  const overdueSection = document.getElementById('revisions-overdue-section');
  if (overdueSection) {
    if (data.overdue.length > 0) {
      overdueSection.classList.remove('hidden');
      overdueContainer.innerHTML = data.overdue.map(r => renderRevisionCard(r, 'overdue')).join('');
    } else {
      overdueSection.classList.add('hidden');
    }
  }

  // Upcoming
  if (upcomingContainer) {
    if (data.upcoming.length === 0) {
      upcomingContainer.innerHTML = `
        <div class="p-4 text-center text-slate-500 font-mono-tactical text-xs">
          NENHUMA REVISÃO FUTURA NO RADAR.
        </div>`;
    } else {
      upcomingContainer.innerHTML = data.upcoming.map(r => renderRevisionCard(r, 'upcoming')).join('');
    }
  }

  // Completed
  if (completedContainer) {
    if (data.completed.length === 0) {
      completedContainer.innerHTML = `
        <div class="p-4 text-center text-slate-500 font-mono-tactical text-xs">
          HISTÓRICO VAZIO.
        </div>`;
    } else {
      completedContainer.innerHTML = data.completed.map(r => renderRevisionCard(r, 'completed')).join('');
    }
  }
}

function renderRevisionCard(r, type) {
  const isCompleted = r.completed === 1;
  const isUrgent = type === 'today' || type === 'overdue';

  return `
    <div class="tactical-card ${isUrgent ? 'tactical-card-red' : ''} p-4 rounded-lg border border-slate-800 mb-3 bg-slate-900/90 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-start space-x-3 flex-1">
        <div class="w-9 h-9 rounded flex items-center justify-center text-white mt-0.5" style="background-color: ${r.subject_color}22; border: 1px solid ${r.subject_color}66">
          <i class="fa-solid ${r.subject_icon || 'fa-book'} text-sm" style="color: ${r.subject_color}"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-slate-100">${escapeHtml(r.title)}</span>
            <span class="tactical-pill bg-blue-950 text-blue-300 border border-blue-800">${r.stage_label}</span>
          </div>
          <div class="text-xs text-slate-400 mt-1">
            <span class="text-slate-300 font-semibold">${escapeHtml(r.subject_name)}</span> 
            ${r.topic_name ? `• <span>${escapeHtml(r.topic_name)}</span>` : ''}
            • Data: <span class="font-mono-tactical ${type === 'overdue' ? 'text-rose-400 font-bold' : 'text-slate-300'}">${r.scheduled_date}</span>
          </div>
          ${r.notes ? `<div class="text-xs text-slate-400 italic mt-1 bg-slate-950/40 p-1.5 rounded border border-slate-800/50">${escapeHtml(r.notes)}</div>` : ''}
        </div>
      </div>

      <div class="flex items-center space-x-2">
        ${!isCompleted ? `
          <button onclick="completeRevision(${r.id})" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-tactical font-semibold flex items-center space-x-1.5 shadow-md shadow-emerald-950">
            <i class="fa-solid fa-check"></i>
            <span>CUMPRIR REVISÃO (QAP!)</span>
          </button>
        ` : `
          <span class="text-xs font-mono-tactical text-emerald-400 bg-emerald-950/60 px-2 py-1 rounded border border-emerald-800">
            ✓ CONCLUÍDA EM ${r.completed_at || ''}
          </span>
        `}
        <button onclick="deleteRevision(${r.id})" class="text-slate-600 hover:text-rose-400 p-1">
          <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
      </div>
    </div>
  `;
}

async function completeRevision(id) {
  try {
    tacticalSound.missionComplete();
    const res = await fetch(`/api/revisions/${id}/complete`, { method: 'POST' });
    const data = await res.json();
    showToast(data.message);
    loadRevisions();
    loadDashboard();
  } catch (err) {
    console.error(err);
  }
}

async function deleteRevision(id) {
  if (!confirm("Deseja remover esta revisão?")) return;
  try {
    await fetch(`/api/revisions/${id}`, { method: 'DELETE' });
    loadRevisions();
  } catch (e) {
    console.error(e);
  }
}

function openAddRevisionModal() {
  const subjSelect = document.getElementById('modal-rev-subject');
  subjSelect.innerHTML = `<option value="">-- SELECIONE A DISCIPLINA --</option>` +
    state.subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

  document.getElementById('modal-rev-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-add-revision').classList.remove('hidden');
}

async function submitAddRevision() {
  const subjectId = parseInt(document.getElementById('modal-rev-subject').value);
  const title = document.getElementById('modal-rev-title').value.trim();
  const date = document.getElementById('modal-rev-date').value;
  const stage = parseInt(document.getElementById('modal-rev-stage').value);
  const notes = document.getElementById('modal-rev-notes').value.trim();

  if (!subjectId || !title || !date) {
    showToast("Preencha todos os campos obrigatórios!");
    return;
  }

  try {
    await fetch('/api/revisions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject_id: subjectId,
        title: title,
        scheduled_date: date,
        interval_stage: stage,
        notes: notes
      })
    });
    document.getElementById('modal-add-revision').classList.add('hidden');
    tacticalSound.beep(1200, 0.05);
    loadRevisions();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== RESET DASHBOARD ====================
function openResetDashboardModal() {
  document.getElementById('modal-reset-dashboard').classList.remove('hidden');
}

async function submitResetDashboard() {
  const resetSessions = document.getElementById('reset-chk-sessions').checked;
  const resetRevisions = document.getElementById('reset-chk-revisions').checked;
  const resetTopics = document.getElementById('reset-chk-topics').checked;
  const resetSims = document.getElementById('reset-chk-sims').checked;

  if (!resetSessions && !resetRevisions && !resetTopics && !resetSims) {
    showToast("Selecione pelo menos um item para zerar.");
    return;
  }

  const confirmAction = confirm(
    "⚠️ ATENÇÃO: Deseja realmente zerar as estatísticas selecionadas?\n" +
    "Esta ação reiniciará os turnos e horas de estudo selecionados."
  );
  if (!confirmAction) return;

  try {
    const res = await fetch('/api/dashboard/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reset_sessions: resetSessions,
        reset_revisions: resetRevisions,
        reset_topics: resetTopics,
        reset_simulations: resetSims
      })
    });

    const data = await res.json();
    if (data.success) {
      tacticalSound.beep(500, 0.15, 'sawtooth');
      closeModal('modal-reset-dashboard');
      showToast(data.message);
      loadDashboard();
      if (resetTopics) loadSubjects();
      if (resetRevisions) loadRevisions();
      if (resetSims) loadSimulations();
    }
  } catch (e) {
    console.error(e);
    showToast("Erro ao zerar o painel.");
  }
}

// ==================== POLICE NEWS FEED ====================
async function loadNews() {
  try {
    const priority = state.newsFilter?.priority || 'all';
    const res = await fetch(`/api/news?priority=${encodeURIComponent(priority)}`);
    const data = await res.json();
    state.news = data;
    renderNews(data);
  } catch (err) {
    console.error("Erro ao carregar notícias:", err);
  }
}

function filterNewsPriority(priority, btn) {
  if (!state.newsFilter) state.newsFilter = { priority: 'all' };
  state.newsFilter.priority = priority;

  document.querySelectorAll('.news-prio-btn').forEach(b => {
    b.classList.remove('bg-[#182338]', 'text-white', 'border-[#2b3d5c]', 'font-bold');
    b.classList.add('bg-[#111722]');
  });
  btn.classList.add('bg-[#182338]', 'text-white', 'border-[#2b3d5c]', 'font-bold');
  btn.classList.remove('bg-[#111722]');

  tacticalSound.beep(1050, 0.03);
  loadNews();
}

function renderNews(newsItems) {
  const container = document.getElementById('news-feed-container');
  if (!container) return;

  if (newsItems.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs">
        NENHUMA NOTÍCIA POLICIAL ENCONTRADA COM ESTE FILTRO. CLIQUE EM 'ATUALIZAR NOTÍCIAS' PARA BUSCAR NOVIDADES.
      </div>`;
    return;
  }

  container.innerHTML = newsItems.map(n => {
    let prioBadge = '';
    if (n.priority === 'alta') {
      prioBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-mono-tactical font-bold bg-rose-950/80 text-rose-300 border border-rose-700/80 flex items-center space-x-1"><span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse"></span><span>🔴 MAIOR: EDITAL ABERTO</span></span>`;
    } else if (n.priority === 'media') {
      prioBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-mono-tactical font-bold bg-amber-950/80 text-amber-300 border border-amber-700/80 flex items-center space-x-1"><span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span><span>⚡ MÉDIA: IMINENTE / BANCA</span></span>`;
    } else {
      prioBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-mono-tactical font-bold bg-[#141b26] text-slate-300 border border-[#232f44] flex items-center space-x-1"><span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span><span>📋 NORMAL: COMISSÕES & TAF</span></span>`;
    }

    return `
      <div class="tactical-card p-4 rounded-lg border border-[#182030] bg-[#0c1017] mb-3 hover:border-[#26334a] transition">
        <div class="flex flex-wrap items-center justify-between gap-2 text-xs mb-2">
          <div class="flex items-center space-x-2">
            ${prioBadge}
            <span class="tactical-pill bg-[#111722] text-slate-300 border border-[#1e293b] text-[10px] uppercase font-bold">
              ${escapeHtml(n.category)}
            </span>
          </div>
          <span class="text-slate-400 font-mono-tactical text-[11px]">${n.pub_date} • ${escapeHtml(n.source)}</span>
        </div>

        <h4 class="text-sm font-bold text-slate-100 hover:text-blue-400 transition mb-1 leading-snug">
          <a href="${n.link || '#'}" target="_blank">${escapeHtml(n.title)}</a>
        </h4>

        <p class="text-xs text-slate-400 leading-relaxed">
          ${escapeHtml(n.summary)}
        </p>

        ${n.link && n.link !== '#' ? `
          <div class="mt-2 text-right">
            <a href="${n.link}" target="_blank" class="text-[11px] font-tactical text-blue-400 hover:underline inline-flex items-center space-x-1">
              <span>LER REPORTAGEM COMPLETA</span>
              <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
            </a>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

async function syncLiveNews() {
  const btn = document.getElementById('btn-sync-news');
  const icon = btn?.querySelector('i');
  if (icon) icon.classList.add('fa-spin');
  tacticalSound.radioChirp();

  try {
    const res = await fetch('/api/news/sync', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      tacticalSound.missionComplete();
      showToast(data.message || `Notícias atualizadas com sucesso!`);
      loadNews();
    } else {
      showToast("Radar sincronizado com a base de concursos!");
      loadNews();
    }
  } catch (e) {
    console.error(e);
  } finally {
    if (icon) icon.classList.remove('fa-spin');
  }
}

// ==================== SIMULATIONS VIEW (A6 - Por Matéria & Nota de Corte) ====================
async function loadSimulations() {
  try {
    const [resSims, resAnalytics] = await Promise.all([
      fetch('/api/simulations'),
      fetch('/api/simulations/analytics')
    ]);
    const data = await resSims.json();
    const analytics = await resAnalytics.json();
    state.simulations = data;
    state.simulationsAnalytics = analytics;
    renderSimulationsAnalytics(analytics);
    renderSimulations(data);
  } catch (err) {
    console.error("Erro ao carregar simulados:", err);
  }
}

function renderSimulationsAnalytics(analytics) {
  const panel = document.getElementById('simulations-analytics-panel');
  if (!panel) return;
  if (!analytics || analytics.total_simulations === 0) {
    panel.classList.add('hidden');
    return;
  }
  panel.classList.remove('hidden');

  const avgEl = document.getElementById('sim-avg-score');
  const cutEl = document.getElementById('sim-ref-cutoff');
  if (avgEl) avgEl.innerText = `${analytics.avg_score} pts`;
  if (cutEl) cutEl.innerText = analytics.latest_cutoff > 0 ? `${analytics.latest_cutoff} pts` : '--';

  // Evolution vs Cutoff Chart
  const ctx = document.getElementById('simulationsChart');
  if (ctx && typeof Chart !== 'undefined') {
    if (state.charts.simulationsChart) state.charts.simulationsChart.destroy();
    const labels = analytics.trend.map(t => `${t.date.slice(5)} (${t.title.slice(0, 14)})`);
    const scores = analytics.trend.map(t => t.score);
    const cutoffs = analytics.trend.map(t => (t.cutoff_score > 0 ? t.cutoff_score : null));
    const hasCutoff = cutoffs.some(c => c !== null);

    const datasets = [{
      label: 'Sua Nota Líquida',
      data: scores,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.18)',
      fill: true,
      tension: 0.28,
      pointRadius: 4,
      pointBackgroundColor: '#60a5fa'
    }];

    if (hasCutoff) {
      datasets.push({
        label: 'Nota de Corte Estimada',
        data: cutoffs,
        borderColor: '#f59e0b',
        borderDash: [6, 4],
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 3,
        pointBackgroundColor: '#fbbf24'
      });
    }

    state.charts.simulationsChart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 10, family: 'JetBrains Mono' } } }
        },
        scales: {
          x: { grid: { color: 'rgba(30,41,59,0.35)' }, ticks: { color: '#64748b', font: { size: 9 } } },
          y: { beginAtZero: true, grid: { color: 'rgba(30,41,59,0.35)' }, ticks: { color: '#64748b', font: { size: 10 } } }
        }
      }
    });
  }

  // Per-subject accumulated performance
  const subjBox = document.getElementById('simulations-subject-analytics');
  if (subjBox) {
    if (!analytics.by_subject || analytics.by_subject.length === 0) {
      subjBox.innerHTML = `<div class="text-xs text-slate-500 font-mono-tactical text-center py-6">Lance o desempenho por matéria ao registrar um simulado para ver seu ranking aqui.</div>`;
    } else {
      subjBox.innerHTML = analytics.by_subject.map(item => {
        const barColor = item.accuracy_pct >= 75 ? 'bg-emerald-500' : (item.accuracy_pct >= 60 ? 'bg-amber-500' : 'bg-rose-500');
        const textColor = item.accuracy_pct >= 75 ? 'text-emerald-400' : (item.accuracy_pct >= 60 ? 'text-amber-400' : 'text-rose-400');
        return `
          <div class="p-2 rounded bg-[#07090e] border border-[#182030]">
            <div class="flex items-center justify-between text-[11px] mb-1">
              <span class="font-semibold text-slate-200 truncate pr-2">${escapeHtml(item.subject_name)}</span>
              <span class="font-mono-tactical font-bold ${textColor} shrink-0">${item.accuracy_pct}% (${item.correct}/${item.total})</span>
            </div>
            <div class="w-full bg-[#111722] h-1.5 rounded-full overflow-hidden">
              <div class="h-full ${barColor}" style="width: ${Math.min(100, item.accuracy_pct)}%"></div>
            </div>
          </div>
        `;
      }).join('');
    }
  }
}

function renderSimulations(sims) {
  const container = document.getElementById('simulations-list');
  if (!container) return;

  if (sims.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded">
        NENHUM SIMULADO REGISTRADO AINDA. TESTE SUA PREPARAÇÃO EM COMBATE!
      </div>`;
    return;
  }

  container.innerHTML = sims.map(s => {
    const pct = s.total_questions > 0 ? Math.round((s.correct_answers / s.total_questions) * 100) : 0;
    const cutoff = Number(s.cutoff_score || 0);
    const cutoffPill = cutoff > 0
      ? (s.score >= cutoff
          ? `<span class="tactical-pill bg-emerald-950 text-emerald-300 border border-emerald-700 text-[9px] font-bold">ACIMA DO CORTE (${cutoff} pts)</span>`
          : `<span class="tactical-pill bg-rose-950 text-rose-300 border border-rose-700 text-[9px] font-bold">FALTAM ${(cutoff - s.score).toFixed(1)} pts P/ CORTE (${cutoff})</span>`)
      : '';
    const breakdown = Array.isArray(s.subject_breakdown) ? s.subject_breakdown : [];
    const breakdownHtml = breakdown.length > 0 ? `
      <div class="w-full pt-2.5 mt-2.5 border-t border-slate-800/80 flex flex-wrap gap-1.5">
        ${breakdown.map(b => {
          const tot = Number(b.total || (Number(b.correct || 0) + Number(b.wrong || 0)));
          const bpct = tot > 0 ? Math.round((Number(b.correct || 0) / tot) * 100) : 0;
          const cls = bpct >= 75 ? 'border-emerald-800/60 text-emerald-300 bg-emerald-950/30' : (bpct >= 60 ? 'border-amber-800/60 text-amber-300 bg-amber-950/30' : 'border-rose-800/60 text-rose-300 bg-rose-950/30');
          return `<span class="text-[10px] font-mono-tactical px-2 py-0.5 rounded border ${cls}">${escapeHtml(b.subject_name)}: ${b.correct}/${tot} (${bpct}%)</span>`;
        }).join('')}
      </div>
    ` : '';

    return `
      <div class="tactical-card p-4 rounded-lg border border-slate-800 bg-slate-900/90 mb-3">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h4 class="text-sm font-bold text-slate-100">${escapeHtml(s.title)}</h4>
              ${s.target_contest ? `<span class="tactical-pill bg-blue-950 text-blue-300 border border-blue-800">${escapeHtml(s.target_contest)}</span>` : ''}
              ${cutoffPill}
            </div>
            <div class="text-xs text-slate-400 mt-1">
              Data: <span class="font-mono-tactical text-slate-300">${escapeHtml(s.date)}</span> • 
              Total de Itens: <span class="font-mono-tactical text-slate-300">${s.total_questions}</span>
            </div>
            ${s.notes ? `<div class="text-xs text-slate-500 mt-1 italic">${escapeHtml(s.notes)}</div>` : ''}
          </div>

          <div class="flex items-center space-x-6 text-right">
            <div>
              <div class="font-mono-tactical text-base font-bold text-emerald-400">${s.correct_answers} / ${s.total_questions}</div>
              <div class="text-xs text-slate-500">${pct}% de Aproveitamento</div>
            </div>
            <div>
              <div class="font-mono-tactical text-base font-bold text-blue-400">${s.score} pts</div>
              <div class="text-xs text-slate-500">Nota Líquida</div>
            </div>
            <div class="flex items-center space-x-1">
              <button onclick="openEditSimulationModal(${s.id})" class="text-slate-500 hover:text-blue-400 p-1.5 transition" title="Editar simulado">
                <i class="fa-solid fa-pencil text-xs"></i>
              </button>
              <button onclick="deleteSimulation(${s.id})" class="text-slate-600 hover:text-rose-400 p-1.5 transition" title="Excluir simulado">
                <i class="fa-solid fa-trash-can text-xs"></i>
              </button>
            </div>
          </div>
        </div>
        ${breakdownHtml}
      </div>
    `;
  }).join('');
}

function addSimBreakdownRow(mode, preset = null) {
  const containerId = mode === 'edit' ? 'modal-edit-sim-breakdown-rows' : 'modal-sim-breakdown-rows';
  const container = document.getElementById(containerId);
  if (!container) return;
  const row = document.createElement('div');
  row.className = 'sim-breakdown-row grid grid-cols-12 gap-1.5 items-center';
  const subjOptions = (state.subjects || []).map(sub => {
    const sel = preset && (preset.subject_id == sub.id || preset.subject_name === sub.name) ? 'selected' : '';
    return `<option value="${escapeHtml(sub.name)}" data-id="${sub.id}" ${sel}>${escapeHtml(sub.name)}</option>`;
  }).join('');
  const customOpt = (preset && preset.subject_name && !(state.subjects || []).some(sub => sub.name === preset.subject_name))
    ? `<option value="${escapeHtml(preset.subject_name)}" selected>${escapeHtml(preset.subject_name)}</option>` : '';
  row.innerHTML = `
    <select class="sim-br-subj col-span-6 bg-[#0c1017] border border-[#182030] rounded px-1.5 py-1 text-[11px] text-slate-200">${customOpt}${subjOptions}</select>
    <input type="number" min="0" placeholder="Acertos" value="${preset ? (preset.correct ?? '') : ''}" class="sim-br-correct col-span-2 bg-[#0c1017] border border-[#182030] rounded px-1.5 py-1 text-[11px] font-mono-tactical text-emerald-300 text-center" title="Acertos">
    <input type="number" min="0" placeholder="Erros" value="${preset ? (preset.wrong ?? '') : ''}" class="sim-br-wrong col-span-2 bg-[#0c1017] border border-[#182030] rounded px-1.5 py-1 text-[11px] font-mono-tactical text-rose-300 text-center" title="Erros">
    <input type="number" min="0" placeholder="Tot" value="${preset ? (preset.total ?? '') : ''}" class="sim-br-total col-span-1 bg-[#0c1017] border border-[#182030] rounded px-1 py-1 text-[11px] font-mono-tactical text-slate-300 text-center" title="Total (opcional)">
    <button type="button" onclick="this.closest('.sim-breakdown-row').remove()" class="col-span-1 text-slate-500 hover:text-rose-400 text-center"><i class="fa-solid fa-xmark text-xs"></i></button>
  `;
  container.appendChild(row);
}

function collectSimBreakdown(mode) {
  const containerId = mode === 'edit' ? 'modal-edit-sim-breakdown-rows' : 'modal-sim-breakdown-rows';
  const container = document.getElementById(containerId);
  if (!container) return [];
  const list = [];
  container.querySelectorAll('.sim-breakdown-row').forEach(row => {
    const sel = row.querySelector('.sim-br-subj');
    const name = sel ? sel.value.trim() : '';
    const opt = sel && sel.selectedOptions ? sel.selectedOptions[0] : null;
    const subjId = opt && opt.dataset.id ? parseInt(opt.dataset.id) : null;
    const correct = parseInt(row.querySelector('.sim-br-correct').value) || 0;
    const wrong = parseInt(row.querySelector('.sim-br-wrong').value) || 0;
    const totalInput = parseInt(row.querySelector('.sim-br-total').value) || 0;
    const total = totalInput > 0 ? totalInput : (correct + wrong);
    if (name && total > 0) {
      list.push({ subject_id: subjId, subject_name: name, correct, wrong, total });
    }
  });
  return list;
}

async function openEditSimulationModal(id) {
  try {
    const res = await fetch(`/api/simulations/${id}`);
    if (!res.ok) throw new Error("Erro ao buscar dados do simulado");
    const s = await res.json();

    document.getElementById('modal-edit-sim-id').value = s.id;
    document.getElementById('modal-edit-sim-title').value = s.title || '';
    document.getElementById('modal-edit-sim-date').value = s.date || '';
    document.getElementById('modal-edit-sim-target').value = s.target_contest || '';
    document.getElementById('modal-edit-sim-total').value = s.total_questions || 0;
    document.getElementById('modal-edit-sim-correct').value = s.correct_answers || 0;
    document.getElementById('modal-edit-sim-wrong').value = s.wrong_answers || 0;
    document.getElementById('modal-edit-sim-score').value = s.score || 0;
    const cutEl = document.getElementById('modal-edit-sim-cutoff');
    if (cutEl) cutEl.value = s.cutoff_score || '';
    document.getElementById('modal-edit-sim-notes').value = s.notes || '';

    const brContainer = document.getElementById('modal-edit-sim-breakdown-rows');
    if (brContainer) {
      brContainer.innerHTML = '';
      (s.subject_breakdown || []).forEach(item => addSimBreakdownRow('edit', item));
    }

    tacticalSound.beep(1100, 0.04);
    document.getElementById('modal-edit-simulation').classList.remove('hidden');
  } catch (err) {
    showToast("Falha ao abrir simulado para edição: " + err.message, "error");
  }
}

function calculateEditSimScore() {
  const total = parseInt(document.getElementById('modal-edit-sim-total').value) || 0;
  const correct = parseInt(document.getElementById('modal-edit-sim-correct').value) || 0;
  const wrong = parseInt(document.getElementById('modal-edit-sim-wrong').value) || 0;
  const score = Math.max(0, correct - wrong);
  document.getElementById('modal-edit-sim-score').value = score;
}

async function submitEditSimulation() {
  const id = document.getElementById('modal-edit-sim-id').value;
  const title = document.getElementById('modal-edit-sim-title').value.trim();
  const date = document.getElementById('modal-edit-sim-date').value;
  const target = document.getElementById('modal-edit-sim-target').value.trim();
  const total = parseInt(document.getElementById('modal-edit-sim-total').value) || 0;
  const correct = parseInt(document.getElementById('modal-edit-sim-correct').value) || 0;
  const wrong = parseInt(document.getElementById('modal-edit-sim-wrong').value) || 0;
  const score = parseFloat(document.getElementById('modal-edit-sim-score').value) || 0;
  const cutEl = document.getElementById('modal-edit-sim-cutoff');
  const cutoff = cutEl ? (parseFloat(cutEl.value) || 0) : 0;
  const notes = document.getElementById('modal-edit-sim-notes').value.trim();
  const subject_breakdown = collectSimBreakdown('edit');

  if (!title || total <= 0) {
    showToast("Informe o título e número de questões!", "warning");
    return;
  }

  try {
    const payload = {
      title,
      date: date || undefined,
      total_questions: total,
      correct_answers: correct,
      wrong_answers: wrong,
      score,
      cutoff_score: cutoff,
      target_contest: target,
      notes,
      subject_breakdown
    };

    const res = await fetch(`/api/simulations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      tacticalSound.missionComplete();
      closeModal('modal-edit-simulation');
      showToast("Simulado atualizado com sucesso!", "success");
      loadSimulations();
    } else {
      const err = await res.json();
      showToast("Erro ao atualizar simulado: " + (err.detail || "Erro inesperado"), "error");
    }
  } catch (e) {
    console.error(e);
    showToast("Erro na conexão com o servidor", "error");
  }
}

async function deleteSimulation(id) {
  if (!confirm("Deseja excluir este simulado?")) return;
  try {
    await fetch(`/api/simulations/${id}`, { method: 'DELETE' });
    showToast("Simulado excluído.", "info");
    loadSimulations();
  } catch (e) {
    console.error(e);
  }
}

function openAddSimulationModal() {
  document.getElementById('modal-sim-date').value = new Date().toISOString().split('T')[0];
  const brContainer = document.getElementById('modal-sim-breakdown-rows');
  if (brContainer) brContainer.innerHTML = '';
  document.getElementById('modal-add-simulation').classList.remove('hidden');
}

async function submitAddSimulation() {
  const title = document.getElementById('modal-sim-title').value.trim();
  const date = document.getElementById('modal-sim-date').value;
  const target = document.getElementById('modal-sim-target').value.trim();
  const total = parseInt(document.getElementById('modal-sim-total').value) || 0;
  const correct = parseInt(document.getElementById('modal-sim-correct').value) || 0;
  const wrong = parseInt(document.getElementById('modal-sim-wrong').value) || 0;
  const score = parseFloat(document.getElementById('modal-sim-score').value) || 0;
  const cutEl = document.getElementById('modal-sim-cutoff');
  const cutoff = cutEl ? (parseFloat(cutEl.value) || 0) : 0;
  const notes = document.getElementById('modal-sim-notes').value.trim();
  const subject_breakdown = collectSimBreakdown('add');

  if (!title || total <= 0) {
    showToast("Informe o título e número de questões!", "warning");
    return;
  }

  try {
    await fetch('/api/simulations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title, date, total_questions: total,
        correct_answers: correct, wrong_answers: wrong,
        score: score, cutoff_score: cutoff,
        target_contest: target, notes: notes,
        subject_breakdown
      })
    });
    document.getElementById('modal-add-simulation').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast("Simulado registrado nas Métricas de Combate!", "success");
    loadSimulations();
  } catch (e) {
    console.error(e);
    showToast("Erro ao salvar simulado.", "error");
  }
}

// ==================== PROFILE SETTINGS ====================
function openProfileModal() {
  if (state.profile) {
    document.getElementById('modal-profile-name').value = state.profile.name || '';
    document.getElementById('modal-profile-target').value = state.profile.target_role || '';
    document.getElementById('modal-profile-daily').value = (state.profile.daily_goal_minutes / 60).toFixed(1);
    document.getElementById('modal-profile-weekly').value = state.profile.weekly_goal_hours || 25;
    document.getElementById('modal-profile-sound').checked = state.soundEnabled;
  }
  const adminPanel = document.getElementById('admin-users-panel');
  if (adminPanel) {
    if (state.currentUser && state.currentUser.is_admin === 1) {
      adminPanel.classList.remove('hidden');
      loadAdminUsers();
    } else {
      adminPanel.classList.add('hidden');
    }
  }
  document.getElementById('modal-profile').classList.remove('hidden');
}

async function loadAdminUsers() {
  const listEl = document.getElementById('admin-users-list');
  if (!listEl) return;
  try {
    const res = await fetch('/api/admin/users');
    if (!res.ok) return;
    const users = await res.json();
    listEl.innerHTML = users.map(u => `
      <div class="p-2 rounded bg-[#07090e] border border-[#182030] flex flex-wrap items-center justify-between gap-2">
        <div class="min-w-0">
          <div class="flex items-center space-x-1.5">
            <span class="text-xs font-bold text-slate-100">${escapeHtml(u.display_name)}</span>
            <span class="text-[10px] font-mono-tactical text-slate-400">@${escapeHtml(u.username)}</span>
            ${u.is_admin ? `<span class="text-[9px] px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-600/40 font-mono-tactical">ADMIN</span>` : ''}
          </div>
          <div class="text-[10px] text-slate-500 truncate">${escapeHtml(u.target_role || 'Sem alvo definido')}</div>
        </div>
        <div class="flex items-center space-x-1.5">
          <input type="text" id="admin-pwd-${u.id}" placeholder="Nova senha" class="w-24 bg-[#0c1017] border border-[#232f44] rounded px-1.5 py-1 text-[11px] text-slate-200">
          <button type="button" onclick="adminResetUserPassword(${u.id}, '${escapeHtml(u.username).replace(/'/g, "\\'")}')" class="px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded text-[10px] font-tactical font-bold">
            REDEFINIR
          </button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Erro ao carregar usuários:', e);
  }
}

async function adminResetUserPassword(userId, username) {
  const input = document.getElementById(`admin-pwd-${userId}`);
  const newPassword = input ? input.value.trim() : '';
  if (newPassword.length < 4) {
    showToast('A nova senha provisória precisa ter pelo menos 4 caracteres.', 'warning');
    return;
  }
  try {
    const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_password: newPassword })
    });
    const data = await res.json();
    if (res.ok) {
      if (input) input.value = '';
      tacticalSound.missionComplete();
      showToast(`Senha de @${username} redefinida! Já pode repassar ao usuário.`, 'success', 5000);
    } else {
      showToast(data.detail || 'Erro ao redefinir senha.', 'error');
    }
  } catch (e) {
    showToast('Erro de conexão ao redefinir senha.', 'error');
  }
}

async function submitProfileUpdate() {
  const name = document.getElementById('modal-profile-name').value.trim();
  const target = document.getElementById('modal-profile-target').value.trim();
  const dailyHrs = parseFloat(document.getElementById('modal-profile-daily').value) || 4;
  const weeklyHrs = parseInt(document.getElementById('modal-profile-weekly').value) || 25;
  const sound = document.getElementById('modal-profile-sound').checked ? 1 : 0;

  try {
    await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        target_role: target,
        daily_goal_minutes: Math.round(dailyHrs * 60),
        weekly_goal_hours: weeklyHrs,
        sound_enabled: sound
      })
    });
    state.soundEnabled = sound === 1;
    document.getElementById('modal-profile').classList.add('hidden');
    tacticalSound.beep(1200, 0.05);
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== ARSENAL TÁTICO: PLATAFORMAS & VÍDEOS ====================
async function loadPlatforms(filterCat = 'all') {
  try {
    const res = await fetch(`/api/platforms?category=${filterCat}`);
    const data = await res.json();
    state.platforms = data;
    renderPlatforms(data);
    renderTimerQuickPlatforms();
  } catch (err) {
    console.error("Erro ao carregar plataformas:", err);
  }
}

function renderPlatforms(platforms) {
  const container = document.getElementById('platforms-grid-container');
  if (!container) return;

  if (platforms.length === 0) {
    container.innerHTML = `
      <div class="col-span-full p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
        NENHUMA PLATAFORMA ENCONTRADA. CLIQUE EM "+ ADICIONAR PLATAFORMA".
      </div>`;
    return;
  }

  container.innerHTML = platforms.map(p => `
    <div class="tactical-card platform-card p-5 rounded-xl border border-slate-800/90 flex flex-col justify-between hover:border-blue-600 transition group">
      <div>
        <div class="flex items-center justify-between gap-2 mb-3">
          <span class="tactical-pill bg-slate-900 text-slate-300 border border-slate-700/80">
            ${escapeHtml(p.category)}
          </span>
          <div class="flex items-center space-x-1">
            <button onclick="deletePlatform(${p.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir plataforma">
              <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
          </div>
        </div>

        <div class="flex items-start space-x-3.5 mb-3">
          <div class="w-11 h-11 rounded-lg flex items-center justify-center text-white shrink-0 shadow-lg" style="background-color: ${p.color || '#3b82f6'}20; border: 1px solid ${p.color || '#3b82f6'}60">
            <i class="fa-solid ${p.icon || 'fa-globe'} text-lg" style="color: ${p.color || '#3b82f6'}"></i>
          </div>
          <div>
            <h3 class="text-base font-bold text-slate-100 group-hover:text-blue-400 transition leading-snug">
              ${escapeHtml(p.title)}
            </h3>
            <div class="text-[11px] font-mono-tactical text-slate-400 truncate max-w-[200px] mt-0.5">
              ${p.url.replace(/^https?:\/\//, '')}
            </div>
          </div>
        </div>

        <p class="text-xs text-slate-400 leading-relaxed mb-4 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
          ${escapeHtml(p.notes || 'Acesso rápido para videoaulas e resolução intensiva de questões.')}
        </p>
      </div>

      <div class="pt-3 border-t border-slate-800/80">
        <a href="${p.url}" target="_blank" class="w-full py-2 bg-blue-600/90 hover:bg-blue-600 text-white rounded-lg text-xs font-tactical font-semibold flex items-center justify-center space-x-2 shadow-md shadow-blue-950 transition">
          <span>ACESSAR PLATAFORMA</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[11px]"></i>
        </a>
      </div>
    </div>
  `).join('');
}

function filterPlatforms(category, btn) {
  document.querySelectorAll('.platform-filter-btn').forEach(b => {
    b.classList.remove('bg-blue-600', 'text-white');
    b.classList.add('bg-slate-900', 'text-slate-400');
  });
  btn.classList.add('bg-blue-600', 'text-white');
  btn.classList.remove('bg-slate-900', 'text-slate-400');
  tacticalSound.beep(1100, 0.03);
  loadPlatforms(category);
}

function renderTimerQuickPlatforms() {
  const container = document.getElementById('timer-quick-platforms-dock');
  if (!container || !state.platforms) return;

  const pinned = state.platforms.slice(0, 6);
  container.innerHTML = pinned.map(p => `
    <a href="${p.url}" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/80 text-xs font-tactical flex items-center space-x-2 text-slate-300 transition shrink-0" title="${escapeHtml(p.title)}">
      <i class="fa-solid ${p.icon || 'fa-globe'} text-xs" style="color: ${p.color || '#3b82f6'}"></i>
      <span>${escapeHtml(p.title)}</span>
      <i class="fa-solid fa-arrow-up-right-from-square text-[9px] text-slate-500"></i>
    </a>
  `).join('');
}

function openAddPlatformModal() {
  document.getElementById('modal-platform-title').value = '';
  document.getElementById('modal-platform-url').value = '';
  document.getElementById('modal-platform-notes').value = '';
  document.getElementById('modal-add-platform').classList.remove('hidden');
}

async function submitAddPlatform() {
  const title = document.getElementById('modal-platform-title').value.trim();
  const url = document.getElementById('modal-platform-url').value.trim();
  const category = document.getElementById('modal-platform-category').value;
  const icon = document.getElementById('modal-platform-icon').value;
  const color = document.getElementById('modal-platform-color').value;
  const notes = document.getElementById('modal-platform-notes').value.trim();

  if (!title || !url) {
    showToast("Informe o título e o link (URL) da plataforma!");
    return;
  }

  try {
    const res = await fetch('/api/platforms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, url, category, icon, color, notes })
    });
    const data = await res.json();
    document.getElementById('modal-add-platform').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadPlatforms();
  } catch (e) {
    console.error(e);
    showToast("Erro ao adicionar plataforma.");
  }
}

async function deletePlatform(id) {
  if (!confirm("Deseja remover esta plataforma do seu Arsenal Tático?")) return;
  try {
    await fetch(`/api/platforms/${id}`, { method: 'DELETE' });
    tacticalSound.beep(800, 0.04);
    loadPlatforms();
  } catch (e) {
    console.error(e);
  }
}

// ==================== COUNTDOWN (DIA D) ====================
function initCountdown(countdown) {
  if (state.countdownIntervalId) clearInterval(state.countdownIntervalId);

  const titleEl = document.getElementById('hud-countdown-title');
  const daysEl = document.getElementById('hud-countdown-days');
  const hoursEl = document.getElementById('hud-countdown-hours');
  const minsEl = document.getElementById('hud-countdown-mins');
  const secsEl = document.getElementById('hud-countdown-secs');
  const targetLabelEl = document.getElementById('hud-countdown-target-date');

  if (titleEl) titleEl.innerText = countdown.title || 'OPERAÇÃO DIA D';
  if (targetLabelEl) targetLabelEl.innerText = `${countdown.target_date} às ${countdown.target_time || '08:00'}`;

  const targetDate = new Date(`${countdown.target_date}T${countdown.target_time || '08:00'}:00`);

  function update() {
    const now = new Date();
    const diff = targetDate - now;

    if (diff <= 0) {
      if (daysEl) daysEl.innerText = '00';
      if (hoursEl) hoursEl.innerText = '00';
      if (minsEl) minsEl.innerText = '00';
      if (secsEl) secsEl.innerText = '00';
      return;
    }

    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
    const m = Math.floor((diff / 1000 / 60) % 60);
    const s = Math.floor((diff / 1000) % 60);

    const pad = (n) => String(n).padStart(2, '0');
    if (daysEl) daysEl.innerText = pad(d);
    if (hoursEl) hoursEl.innerText = pad(h);
    if (minsEl) minsEl.innerText = pad(m);
    if (secsEl) secsEl.innerText = pad(s);
  }

  update();
  state.countdownIntervalId = setInterval(update, 1000);
}

function openEditCountdownModal() {
  if (state.dashboardData && state.dashboardData.countdown) {
    document.getElementById('modal-countdown-title').value = state.dashboardData.countdown.title || '';
    document.getElementById('modal-countdown-date').value = state.dashboardData.countdown.target_date || '';
    document.getElementById('modal-countdown-time').value = state.dashboardData.countdown.target_time || '08:00';
  }
  document.getElementById('modal-edit-countdown').classList.remove('hidden');
}

async function submitUpdateCountdown() {
  const title = document.getElementById('modal-countdown-title').value.trim();
  const date = document.getElementById('modal-countdown-date').value;
  const time = document.getElementById('modal-countdown-time').value || '08:00';

  if (!title || !date) {
    showToast("Informe o nome do concurso e a data do Dia D!");
    return;
  }

  try {
    const res = await fetch('/api/countdown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, target_date: date, target_time: time })
    });
    const data = await res.json();
    document.getElementById('modal-edit-countdown').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== QUADRO DE HONRA (APROVAÇÕES) ====================
async function loadApprovals() {
  try {
    const res = await fetch('/api/approvals');
    const data = await res.json();
    state.approvals = data;
    renderApprovals(data);
  } catch (err) {
    console.error("Erro ao carregar aprovações:", err);
  }
}

function renderApprovals(approvals) {
  const container = document.getElementById('approvals-grid-container');
  if (!container) return;

  if (approvals.length === 0) {
    container.innerHTML = `
      <div class="col-span-full p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
        NENHUMA CONQUISTA REGISTRADA AINDA. CADASTRAR SUA PRIMEIRA VITÓRIA FORTALECE SUA MENTE OPERACIONAL!
      </div>`;
    return;
  }

  container.innerHTML = approvals.map(a => `
    <div class="tactical-card p-5 rounded-xl border border-amber-900/60 bg-gradient-to-b from-[#0e1626] to-[#070b14] flex flex-col justify-between hover:border-amber-500/80 transition relative overflow-hidden group">
      <div class="absolute -right-3 -bottom-3 text-amber-500/5 text-8xl font-black pointer-events-none">
        <i class="fa-solid fa-trophy"></i>
      </div>

      <div>
        <div class="flex items-center justify-between gap-2 mb-3">
          <span class="tactical-pill bg-amber-950/80 text-amber-300 border border-amber-800/90 flex items-center space-x-1.5">
            <i class="fa-solid fa-medal text-xs text-amber-400"></i>
            <span>${escapeHtml(a.status)}</span>
          </span>
          <div class="flex items-center space-x-1">
            <span class="font-mono-tactical text-xs text-slate-400">${a.year}</span>
            <button onclick="deleteApproval(${a.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir aprovação">
              <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
          </div>
        </div>

        <h3 class="text-base font-bold text-slate-100 group-hover:text-amber-300 transition leading-snug mb-1">
          ${escapeHtml(a.contest_name)}
        </h3>
        <p class="text-xs text-blue-400 font-semibold mb-3">${escapeHtml(a.role)}</p>

        <div class="grid grid-cols-2 gap-2 text-xs bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/70 mb-3">
          <div>
            <span class="text-slate-500 block text-[10px]">Colocação / Posição</span>
            <span class="font-mono-tactical text-slate-200 font-bold">${escapeHtml(a.position || 'Classificado')}</span>
          </div>
          <div>
            <span class="text-slate-500 block text-[10px]">Nota / Pontuação</span>
            <span class="font-mono-tactical text-emerald-400 font-bold">${escapeHtml(a.score || 'Aprovado')}</span>
          </div>
        </div>

        ${a.notes ? `
          <p class="text-xs text-slate-400 italic bg-slate-950/40 p-2 rounded border border-slate-800/40 mb-2">
            "${escapeHtml(a.notes)}"
          </p>
        ` : ''}
      </div>

      <div class="pt-2 text-right">
        <span class="text-[10px] font-mono-tactical text-amber-500/80 tracking-wider">REGISTRO DE HONRA VALIDADO ✓</span>
      </div>
    </div>
  `).join('');
}

function openAddApprovalModal() {
  document.getElementById('modal-approval-contest').value = '';
  document.getElementById('modal-approval-role').value = '';
  document.getElementById('modal-approval-year').value = new Date().getFullYear();
  document.getElementById('modal-approval-pos').value = '';
  document.getElementById('modal-approval-score').value = '';
  document.getElementById('modal-approval-notes').value = '';
  document.getElementById('modal-add-approval').classList.remove('hidden');
}

async function submitAddApproval() {
  const contest = document.getElementById('modal-approval-contest').value.trim();
  const role = document.getElementById('modal-approval-role').value.trim();
  const year = parseInt(document.getElementById('modal-approval-year').value) || new Date().getFullYear();
  const position = document.getElementById('modal-approval-pos').value.trim();
  const score = document.getElementById('modal-approval-score').value.trim();
  const status = document.getElementById('modal-approval-status').value;
  const notes = document.getElementById('modal-approval-notes').value.trim();

  if (!contest || !role) {
    showToast("Informe o concurso e o cargo da aprovação!");
    return;
  }

  try {
    const res = await fetch('/api/approvals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contest_name: contest,
        role: role,
        year: year,
        position: position,
        score: score,
        status: status,
        notes: notes
      })
    });
    const data = await res.json();
    document.getElementById('modal-add-approval').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadApprovals();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

async function deleteApproval(id) {
  if (!confirm("Deseja remover esta aprovação do seu Quadro de Honra?")) return;
  try {
    await fetch(`/api/approvals/${id}`, { method: 'DELETE' });
    loadApprovals();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== MÓDULO TAF (TREINAMENTO FÍSICO) ====================
async function loadTaf() {
  try {
    const res = await fetch('/api/taf');
    const data = await res.json();
    state.tafRecords = data;
    renderTaf(data);
  } catch (err) {
    console.error("Erro ao carregar registros TAF:", err);
  }
}

function renderTaf(records) {
  const container = document.getElementById('taf-history-list');
  const latestSummary = document.getElementById('taf-latest-summary-card');
  if (!container) return;

  if (records.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
        NENHUM SIMULADO OU TREINO TAF REGISTRADO. COMECE HOJE A TREINAR A BARRA E A CORRIDA!
      </div>`;
    return;
  }

  // Latest Test Header Card
  const latest = records[0];
  if (latestSummary) {
    latestSummary.innerHTML = `
      <div class="tactical-card p-5 rounded-xl border ${latest.is_apto ? 'border-emerald-600/80' : 'border-amber-600/80'} bg-slate-900/90 mb-6">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <div class="text-[10px] font-mono-tactical text-slate-400">ÚLTIMO SIMULADO TAF REALIZADO EM ${latest.date}</div>
            <div class="text-base font-bold font-tactical ${latest.is_apto ? 'text-emerald-400' : 'text-amber-400'} flex items-center space-x-2">
              <i class="fa-solid ${latest.is_apto ? 'fa-shield-halved' : 'fa-triangle-exclamation'}"></i>
              <span>${latest.status_label}</span>
            </div>
          </div>
          <span class="tactical-pill ${latest.is_apto ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'bg-amber-950 text-amber-300 border border-amber-700'}">
            PADRÃO POLÍCIA FEDERAL / PRF
          </span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div class="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
            <span class="text-[10px] text-slate-400 block mb-1">BARRA FIXA (MIN. 3)</span>
            <span class="text-xl font-mono-tactical font-bold ${latest.pull_apto ? 'text-emerald-400' : 'text-rose-400'}">${latest.pull_ups} reps</span>
            <span class="text-[10px] block mt-0.5 ${latest.pull_apto ? 'text-emerald-500' : 'text-rose-500'}">${latest.pull_apto ? '✓ Apto' : '✗ Inapto'}</span>
          </div>

          <div class="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
            <span class="text-[10px] text-slate-400 block mb-1">CORRIDA 12M (MIN. 2.000M)</span>
            <span class="text-xl font-mono-tactical font-bold ${latest.run_apto ? 'text-emerald-400' : 'text-rose-400'}">${latest.run_12min_meters} m</span>
            <span class="text-[10px] block mt-0.5 ${latest.run_apto ? 'text-emerald-500' : 'text-rose-500'}">${latest.run_apto ? '✓ Apto' : '✗ Inapto'}</span>
          </div>

          <div class="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
            <span class="text-[10px] text-slate-400 block mb-1">ABDOMINAL 1M (MIN. 36)</span>
            <span class="text-xl font-mono-tactical font-bold ${latest.sit_apto ? 'text-emerald-400' : 'text-rose-400'}">${latest.sit_ups} reps</span>
            <span class="text-[10px] block mt-0.5 ${latest.sit_apto ? 'text-emerald-500' : 'text-rose-500'}">${latest.sit_apto ? '✓ Apto' : '✗ Inapto'}</span>
          </div>

          <div class="bg-slate-950/80 p-3 rounded-lg border border-slate-800/80">
            <span class="text-[10px] text-slate-400 block mb-1">NATAÇÃO 50M (PF MAX 56S)</span>
            <span class="text-xl font-mono-tactical font-bold ${latest.swim_apto ? 'text-emerald-400' : 'text-rose-400'}">${latest.swim_50m_seconds > 0 ? `${latest.swim_50m_seconds}s` : 'N/A'}</span>
            <span class="text-[10px] block mt-0.5 ${latest.swim_apto ? 'text-emerald-500' : 'text-rose-500'}">${latest.swim_50m_seconds > 0 ? (latest.swim_apto ? '✓ Apto' : '✗ Inapto') : 'Opcional'}</span>
          </div>
        </div>
      </div>
    `;
  }

  // History list
  container.innerHTML = records.map(r => `
    <div class="tactical-card p-4 rounded-xl border border-slate-800/80 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3 mb-2.5">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-lg flex items-center justify-center ${r.is_apto ? 'bg-emerald-950 text-emerald-400 border border-emerald-700' : 'bg-amber-950 text-amber-400 border border-amber-700'}">
          <i class="fa-solid fa-person-running text-lg"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-slate-100 font-tactical">${r.date}</span>
            <span class="tactical-pill ${r.is_apto ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'} text-[10px]">
              ${r.is_apto ? 'APTO' : 'INAPTO'}
            </span>
          </div>
          <div class="text-xs text-slate-400 mt-1 flex flex-wrap gap-x-3 gap-y-1">
            <span>Barra: <strong class="text-slate-200">${r.pull_ups}</strong></span>
            <span>Corrida: <strong class="text-slate-200">${r.run_12min_meters}m</strong></span>
            <span>Abdominal: <strong class="text-slate-200">${r.sit_ups}</strong></span>
            ${r.push_ups > 0 ? `<span>Flexão: <strong class="text-slate-200">${r.push_ups}</strong></span>` : ''}
            ${r.swim_50m_seconds > 0 ? `<span>Natação: <strong class="text-slate-200">${r.swim_50m_seconds}s</strong></span>` : ''}
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-3">
        ${r.notes ? `<span class="text-xs text-slate-400 italic max-w-[200px] truncate hidden md:inline">"${escapeHtml(r.notes)}"</span>` : ''}
        <button onclick="deleteTaf(${r.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir treino TAF">
          <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
      </div>
    </div>
  `).join('');
}

function openAddTafModal() {
  document.getElementById('modal-taf-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-taf-pull').value = '5';
  document.getElementById('modal-taf-run').value = '2400';
  document.getElementById('modal-taf-sit').value = '40';
  document.getElementById('modal-taf-push').value = '35';
  document.getElementById('modal-taf-swim').value = '0';
  document.getElementById('modal-taf-notes').value = '';
  document.getElementById('modal-add-taf').classList.remove('hidden');
}

async function submitAddTaf() {
  const date = document.getElementById('modal-taf-date').value;
  const pull = parseInt(document.getElementById('modal-taf-pull').value) || 0;
  const run = parseInt(document.getElementById('modal-taf-run').value) || 0;
  const sit = parseInt(document.getElementById('modal-taf-sit').value) || 0;
  const push = parseInt(document.getElementById('modal-taf-push').value) || 0;
  const swim = parseFloat(document.getElementById('modal-taf-swim').value) || 0.0;
  const isMale = parseInt(document.getElementById('modal-taf-gender').value);
  const notes = document.getElementById('modal-taf-notes').value.trim();

  try {
    const res = await fetch('/api/taf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date, pull_ups: pull, run_12min_meters: run,
        sit_ups: sit, push_ups: push, swim_50m_seconds: swim,
        is_male: isMale, notes
      })
    });
    const data = await res.json();
    document.getElementById('modal-add-taf').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadTaf();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

async function deleteTaf(id) {
  if (!confirm("Deseja excluir este registro de TAF?")) return;
  try {
    await fetch(`/api/taf/${id}`, { method: 'DELETE' });
    loadTaf();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== RADAR DE LEI SECA ====================
async function loadLawReadings() {
  try {
    const res = await fetch('/api/law-readings');
    const data = await res.json();
    state.lawData = data;
    renderLawReadings(data);
  } catch (err) {
    console.error("Erro ao carregar leituras de lei seca:", err);
  }
}

function renderLawReadings(data) {
  const todayCountEl = document.getElementById('law-today-total-display');
  const allTimeCountEl = document.getElementById('law-all-total-display');
  const historyContainer = document.getElementById('law-history-list');
  const breakdownContainer = document.getElementById('law-breakdown-container');

  if (todayCountEl) todayCountEl.innerText = data.today_total || 0;
  if (allTimeCountEl) allTimeCountEl.innerText = data.all_time_total || 0;

  // Breakdown by Code
  if (breakdownContainer) {
    if (!data.breakdown || data.breakdown.length === 0) {
      breakdownContainer.innerHTML = `<span class="text-xs text-slate-500 font-mono-tactical">Nenhuma leitura registrada.</span>`;
    } else {
      breakdownContainer.innerHTML = data.breakdown.map(b => `
        <div class="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-200">${escapeHtml(b.code_name)}</span>
          <span class="font-mono-tactical text-xs font-bold text-blue-400">${b.total_articles} artigos</span>
        </div>
      `).join('');
    }
  }

  // History list
  if (historyContainer) {
    if (!data.logs || data.logs.length === 0) {
      historyContainer.innerHTML = `
        <div class="p-6 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
          NENHUMA LEITURA DE LEI SECA REGISTRADA. LEIA 20 ARTIGOS POR DIA PARA BLINDAR SUA PROVA OBJETIVA!
        </div>`;
      return;
    }

    historyContainer.innerHTML = data.logs.map(l => `
      <div class="tactical-card p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/60 flex items-center justify-between mb-2">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 rounded bg-blue-950 text-blue-400 border border-blue-800 flex items-center justify-center text-xs">
            <i class="fa-solid fa-scale-balanced"></i>
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-xs font-bold text-slate-200">${escapeHtml(l.code_name)}</span>
              <span class="font-mono-tactical text-[11px] text-emerald-400 font-bold">+${l.articles_read} artigos</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-0.5">${escapeHtml(l.notes || 'Leitura de artigos secos da lei')} &bull; <span class="font-mono-tactical text-slate-500">${l.date}</span></div>
          </div>
        </div>
        <button onclick="deleteLawReading(${l.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir">
          <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
      </div>
    `).join('');
  }
}

async function quickAddArticles(count, codeName) {
  tacticalSound.beep(1200, 0.05);
  try {
    const res = await fetch('/api/law-readings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code_name: codeName,
        articles_read: count,
        notes: `Leitura rápida de +${count} artigos`
      })
    });
    const data = await res.json();
    tacticalSound.missionComplete();
    showToast(data.message);
    loadLawReadings();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

function openAddLawModal() {
  document.getElementById('modal-law-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-law-articles').value = '20';
  document.getElementById('modal-law-notes').value = '';
  document.getElementById('modal-add-law').classList.remove('hidden');
}

async function submitAddLaw() {
  const date = document.getElementById('modal-law-date').value;
  const code = document.getElementById('modal-law-code').value;
  const articles = parseInt(document.getElementById('modal-law-articles').value) || 0;
  const notes = document.getElementById('modal-law-notes').value.trim();

  if (articles <= 0) {
    showToast("Informe o número de artigos lidos!");
    return;
  }

  try {
    const res = await fetch('/api/law-readings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, code_name: code, articles_read: articles, notes })
    });
    const data = await res.json();
    document.getElementById('modal-add-law').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadLawReadings();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

async function deleteLawReading(id) {
  if (!confirm("Deseja excluir este registro de leitura?")) return;
  try {
    await fetch(`/api/law-readings/${id}`, { method: 'DELETE' });
    loadLawReadings();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== CICLO TÁTICO AUTOMATIZADO ====================
function startCycleMission(subjectId, topicId) {
  tacticalSound.radioChirp();
  switchTab('timer');
  
  const subjSelect = document.getElementById('timer-subject-select');
  if (subjSelect) {
    subjSelect.value = String(subjectId);
    state.timer.selectedSubjectId = subjectId;
    populateTimerTopicsDropdown(subjectId);
    
    if (topicId) {
      setTimeout(() => {
        const topicSelect = document.getElementById('timer-topic-select');
        if (topicSelect) {
          topicSelect.value = String(topicId);
          state.timer.selectedTopicId = topicId;
        }
      }, 50);
    }
  }
}

// ==================== MODO FOCO SONORO TÁTICO (AMBIENT SOUND) ====================
function toggleAmbientSound() {
  const btn = document.getElementById('btn-toggle-ambient');
  const icon = document.getElementById('ambient-play-icon');
  const wave = document.getElementById('ambient-soundwave-anim');
  const typeSelect = document.getElementById('ambient-type-select');
  const volSlider = document.getElementById('ambient-vol-slider');

  const selectedType = typeSelect ? typeSelect.value : 'brown';
  const vol = volSlider ? parseFloat(volSlider.value) : 0.25;

  if (state.ambientPlaying) {
    tacticalSound.stopAmbient();
    state.ambientPlaying = false;
    if (icon) icon.className = 'fa-solid fa-play';
    if (wave) wave.classList.add('hidden');
    if (btn) btn.classList.replace('bg-emerald-600', 'bg-slate-800');
  } else {
    tacticalSound.startAmbient(selectedType, vol);
    state.ambientPlaying = true;
    if (icon) icon.className = 'fa-solid fa-pause';
    if (wave) wave.classList.remove('hidden');
    if (btn) btn.classList.replace('bg-slate-800', 'bg-emerald-600');
  }
}

function onAmbientTypeChange() {
  if (state.ambientPlaying) {
    const typeSelect = document.getElementById('ambient-type-select');
    const volSlider = document.getElementById('ambient-vol-slider');
    const selectedType = typeSelect ? typeSelect.value : 'brown';
    const vol = volSlider ? parseFloat(volSlider.value) : 0.25;
    tacticalSound.startAmbient(selectedType, vol);
  }
}

function onAmbientVolChange(val) {
  tacticalSound.setAmbientVolume(parseFloat(val));
}

// ==================== CADERNO DE ERROS (DOSSIÊ DE VULNERABILIDADES) ====================
async function loadErrors(banca = 'all', reason = 'all', mastered = null) {
  try {
    let url = `/api/errors?banca=${banca}&reason=${reason}`;
    if (mastered !== null) url += `&mastered=${mastered}`;
    
    const res = await fetch(url);
    const data = await res.json();
    state.errors = data;
    renderErrors(data);
  } catch (e) {
    console.error("Erro ao carregar caderno de erros:", e);
  }
}

function triggerErrorFilters() {
  const b = document.getElementById('filter-error-banca')?.value || 'all';
  const r = document.getElementById('filter-error-reason')?.value || 'all';
  const mVal = document.getElementById('filter-error-mastered')?.value || 'all';
  const m = mVal === 'all' ? null : (mVal === 'true');
  loadErrors(b, r, m);
}

function renderErrors(errors) {
  const container = document.getElementById('errors-list-container');
  if (!container) return;

  if (errors.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
        NENHUM ERRO OU PEGADINHA CATALOGADA. REGISTRE QUESTÕES QUE ERROU PARA NUNCA MAIS PERDER PONTOS!
      </div>`;
    return;
  }

  container.innerHTML = errors.map(e => `
    <div class="tactical-card p-4 rounded-xl border ${e.mastered ? 'border-emerald-800/60 bg-emerald-950/20' : 'border-rose-900/60 bg-slate-900/90'} mb-3 transition" id="error-card-${e.id}">
      <div class="flex flex-wrap items-center justify-between gap-2 mb-2.5">
        <div class="flex items-center space-x-2">
          <span class="tactical-pill bg-slate-800 text-slate-300 border border-slate-700">${escapeHtml(e.banca)}</span>
          <span class="tactical-pill ${e.error_reason === 'Pegadinha de Banca' ? 'bg-amber-950 text-amber-300 border-amber-800' : 'bg-rose-950 text-rose-300 border-rose-800'}">
            ${escapeHtml(e.error_reason)}
          </span>
          ${e.question_ref ? `<span class="text-xs font-mono-tactical text-slate-400">Ref: ${escapeHtml(e.question_ref)}</span>` : ''}
        </div>

        <div class="flex items-center space-x-2">
          <button onclick="toggleErrorMastered(${e.id})" class="px-2.5 py-1 rounded text-xs font-tactical transition flex items-center space-x-1 ${e.mastered ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'bg-slate-800 hover:bg-emerald-900/40 text-slate-400 hover:text-emerald-300 border border-slate-700'}">
            <i class="fa-solid ${e.mastered ? 'fa-check-double text-emerald-400' : 'fa-check'} text-xs"></i>
            <span>${e.mastered ? 'DOMINADO (SUPERADO)' : 'MARCAR COMO DOMINADO'}</span>
          </button>
          <button onclick="openEditErrorModal(${e.id})" class="text-slate-500 hover:text-rose-400 p-1 transition" title="Editar este erro">
            <i class="fa-solid fa-pencil text-xs"></i>
          </button>
          <button onclick="deleteError(${e.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir erro">
            <i class="fa-solid fa-trash-can text-xs"></i>
          </button>
        </div>
      </div>

      <div class="text-xs text-slate-400 mb-2">
        <span class="font-bold text-slate-200">${escapeHtml(e.subject_name)}</span> 
        ${e.topic_name ? `&bull; <span>${escapeHtml(e.topic_name)}</span>` : ''}
      </div>

      ${e.question_statement ? `
        <div class="text-xs text-slate-300 bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 mb-2.5 leading-relaxed font-mono-tactical">
          "${escapeHtml(e.question_statement)}"
        </div>
      ` : ''}

      <div class="bg-amber-950/30 border border-amber-900/40 p-3 rounded-lg text-xs leading-relaxed text-amber-200">
        <div class="font-tactical font-bold text-amber-400 text-[11px] uppercase tracking-wider mb-1 flex items-center space-x-1.5">
          <i class="fa-solid fa-lightbulb"></i>
          <span>BIZU CORRETIVO DA QUESTÃO:</span>
        </div>
        ${escapeHtml(e.bizu_notes)}
      </div>
    </div>
  `).join('');
}

async function toggleErrorMastered(id) {
  tacticalSound.missionComplete();
  try {
    const res = await fetch(`/api/errors/${id}/toggle-mastered`, { method: 'PUT' });
    const data = await res.json();
    showToast(data.message);
    loadErrors();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

function openAddErrorModal() {
  const subjSelect = document.getElementById('modal-error-subject');
  subjSelect.innerHTML = `<option value="">-- SELECIONE A DISCIPLINA --</option>` +
    state.subjects.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

  document.getElementById('modal-error-banca').value = 'Cebraspe';
  document.getElementById('modal-error-ref').value = '';
  document.getElementById('modal-error-statement').value = '';
  document.getElementById('modal-error-bizu').value = '';
  document.getElementById('modal-add-error').classList.remove('hidden');
}

async function submitAddError() {
  const subjectId = parseInt(document.getElementById('modal-error-subject').value);
  const banca = document.getElementById('modal-error-banca').value;
  const reason = document.getElementById('modal-error-reason').value;
  const ref = document.getElementById('modal-error-ref').value.trim();
  const statement = document.getElementById('modal-error-statement').value.trim();
  const bizu = document.getElementById('modal-error-bizu').value.trim();

  if (!subjectId || !bizu) {
    showToast("Selecione a disciplina e preencha o bizu corretivo da questão!");
    return;
  }

  try {
    const res = await fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject_id: subjectId,
        banca, error_reason: reason,
        question_ref: ref,
        question_statement: statement,
        bizu_notes: bizu
      })
    });
    const data = await res.json();
    document.getElementById('modal-add-error').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadErrors();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

async function openEditErrorModal(id) {
  try {
    const res = await fetch(`/api/errors/${id}`);
    if (!res.ok) throw new Error("Erro ao buscar dados do erro");
    const e = await res.json();

    document.getElementById('modal-edit-error-id').value = e.id;

    const subjSelect = document.getElementById('modal-edit-error-subject');
    subjSelect.innerHTML = state.subjects.map(s => `<option value="${s.id}" ${s.id === e.subject_id ? 'selected' : ''}>${s.name}</option>`).join('');

    document.getElementById('modal-edit-error-banca').value = e.banca || 'Cebraspe';
    document.getElementById('modal-edit-error-reason').value = e.error_reason || 'Pegadinha de Banca';
    document.getElementById('modal-edit-error-ref').value = e.question_ref || '';
    document.getElementById('modal-edit-error-statement').value = e.question_statement || '';
    document.getElementById('modal-edit-error-bizu').value = e.bizu_notes || '';

    tacticalSound.beep(1100, 0.04);
    document.getElementById('modal-edit-error').classList.remove('hidden');
  } catch (err) {
    showToast("Falha ao abrir erro para edição: " + err.message);
  }
}

async function submitEditError() {
  const id = document.getElementById('modal-edit-error-id').value;
  const subjectId = parseInt(document.getElementById('modal-edit-error-subject').value);
  const banca = document.getElementById('modal-edit-error-banca').value;
  const reason = document.getElementById('modal-edit-error-reason').value;
  const ref = document.getElementById('modal-edit-error-ref').value.trim();
  const statement = document.getElementById('modal-edit-error-statement').value.trim();
  const bizu = document.getElementById('modal-edit-error-bizu').value.trim();

  if (!subjectId || !bizu) {
    showToast("Selecione a disciplina e preencha o bizu corretivo da questão!");
    return;
  }

  try {
    const payload = {
      subject_id: subjectId,
      banca,
      error_reason: reason,
      question_ref: ref,
      question_statement: statement,
      bizu_notes: bizu
    };

    const res = await fetch(`/api/errors/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      tacticalSound.missionComplete();
      closeModal('modal-edit-error');
      loadErrors();
      loadDashboard();
    } else {
      const err = await res.json();
      showToast("Erro ao atualizar erro: " + (err.detail || "Erro inesperado"));
    }
  } catch (e) {
    console.error(e);
    showToast("Erro na conexão com o servidor");
  }
}

async function deleteError(id) {
  if (!confirm("Deseja remover este registro do caderno de erros?")) return;
  try {
    await fetch(`/api/errors/${id}`, { method: 'DELETE' });
    loadErrors();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== OFICINA DE DISCURSIVAS & REDAÇÕES ====================
async function loadEssays() {
  try {
    const res = await fetch('/api/essays');
    const data = await res.json();
    state.essays = data;
    renderEssays(data);
  } catch (e) {
    console.error("Erro ao carregar redações:", e);
  }
}

function renderEssays(essays) {
  const container = document.getElementById('essays-list-container');
  if (!container) return;

  if (essays.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs border border-dashed border-slate-800 rounded-xl">
        NENHUMA REDAÇÃO REGISTRADA AINDA. TREINE DISCURSIVAS PARA GARANTIR A SUA VAGA NA PROVA!
      </div>`;
    return;
  }

  container.innerHTML = essays.map(e => `
    <div class="tactical-card p-4 rounded-xl border border-slate-800/80 bg-slate-900/90 mb-3 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-start space-x-3.5 flex-1">
        <div class="w-10 h-10 rounded-lg bg-blue-950 text-blue-400 border border-blue-800 flex items-center justify-center shrink-0 mt-0.5">
          <i class="fa-solid fa-pen-nib text-base"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-slate-100 font-tactical">${e.title}</span>
            <span class="tactical-pill bg-slate-800 text-slate-300 border border-slate-700">${e.agency}</span>
          </div>
          <div class="text-xs text-slate-400 mt-1">
            Data: <span class="font-mono-tactical text-slate-300">${e.date}</span> &bull; 
            Linhas escritas: <span class="font-mono-tactical text-slate-300">${e.lines_count} linhas</span>
          </div>
          ${e.notes ? `<div class="text-xs text-slate-400 italic mt-1.5 bg-slate-950/40 p-2 rounded border border-slate-800/40">"${e.notes}"</div>` : ''}
        </div>
      </div>

      <div class="flex items-center space-x-4 text-right">
        <div>
          <div class="text-lg font-mono-tactical font-black text-emerald-400">${e.score} / ${e.max_score}</div>
          <div class="text-[10px] text-slate-500">Nota Obtida</div>
        </div>
        <button onclick="deleteEssay(${e.id})" class="text-slate-600 hover:text-rose-400 p-1 transition" title="Excluir redação">
          <i class="fa-solid fa-trash-can text-xs"></i>
        </button>
      </div>
    </div>
  `).join('');
}

async function loadEssayPrompts() {
  try {
    const res = await fetch('/api/essay-prompts');
    const data = await res.json();
    state.essayPrompts = data;
    renderEssayPrompts(data);
  } catch (e) {
    console.error("Erro ao carregar temas:", e);
  }
}

function renderEssayPrompts(prompts) {
  const container = document.getElementById('essay-prompts-container');
  if (!container) return;

  container.innerHTML = prompts.map(p => `
    <div class="tactical-card p-4 rounded-xl border border-blue-900/40 bg-slate-950/70 hover:border-blue-500/80 transition flex flex-col justify-between">
      <div>
        <div class="flex items-center justify-between text-xs mb-2">
          <span class="tactical-pill bg-blue-950 text-blue-300 border border-blue-800">${p.agency}</span>
          <span class="text-slate-500 font-mono-tactical text-[10px]">${p.axis}</span>
        </div>
        <h4 class="text-xs font-bold text-slate-100 mb-2 leading-relaxed font-tactical">${escapeHtml(p.title)}</h4>
        <p class="text-[11px] text-slate-400 leading-relaxed mb-3">${p.description}</p>
      </div>
      <div class="pt-2 border-t border-slate-800 flex justify-between items-center">
        <button onclick="startEssaySimulator('${encodeURIComponent(p.title)}')" class="text-xs text-emerald-400 hover:text-emerald-300 font-tactical flex items-center space-x-1">
          <i class="fa-solid fa-stopwatch text-[11px]"></i>
          <span>SIMULAR 60 MINUTOS</span>
        </button>
        <button onclick="openAddEssayModal('${encodeURIComponent(p.title)}')" class="text-xs text-blue-400 hover:text-blue-300 font-tactical">
          REGISTRAR NOTA →
        </button>
      </div>
    </div>
  `).join('');
}

function startEssaySimulator(encodedTitle) {
  const title = decodeURIComponent(encodedTitle);
  tacticalSound.radioChirp();
  switchTab('timer');
  setTimerMode('pomodoro');
  setPomodoroPreset(50); // or 60m focus
  state.timer.seconds = 60 * 60;
  updateTimerDisplay();
  document.getElementById('timer-session-label').innerText = `SIMULAÇÃO DE DISCURSIVA: ${title.slice(0, 45)}...`;
  showToast(`Iniciando simulação de redação (60 minutos):\n"${title}"\n\nPegue sua folha de rascunho, caneta preta e bom combate!`);
  startTimer();
}

function openAddEssayModal(prefillTitle = '') {
  document.getElementById('modal-essay-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-essay-title').value = prefillTitle ? decodeURIComponent(prefillTitle) : '';
  document.getElementById('modal-essay-score').value = '18.0';
  document.getElementById('modal-essay-max').value = '20.0';
  document.getElementById('modal-essay-lines').value = '30';
  document.getElementById('modal-essay-notes').value = '';
  document.getElementById('modal-add-essay').classList.remove('hidden');
}

async function submitAddEssay() {
  const title = document.getElementById('modal-essay-title').value.trim();
  const date = document.getElementById('modal-essay-date').value;
  const agency = document.getElementById('modal-essay-agency').value;
  const lines = parseInt(document.getElementById('modal-essay-lines').value) || 30;
  const score = parseFloat(document.getElementById('modal-essay-score').value) || 0.0;
  const maxScore = parseFloat(document.getElementById('modal-essay-max').value) || 20.0;
  const notes = document.getElementById('modal-essay-notes').value.trim();

  if (!title) {
    showToast("Informe o tema da redação!");
    return;
  }

  try {
    const res = await fetch('/api/essays', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title, date, agency, lines_count: lines, score, max_score: maxScore, notes
      })
    });
    const data = await res.json();
    document.getElementById('modal-add-essay').classList.add('hidden');
    tacticalSound.missionComplete();
    showToast(data.message);
    loadEssays();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

async function deleteEssay(id) {
  if (!confirm("Deseja excluir este registro de redação?")) return;
  try {
    await fetch(`/api/essays/${id}`, { method: 'DELETE' });
    loadEssays();
    loadDashboard();
  } catch (e) {
    console.error(e);
  }
}

// ==================== BACKUP & RELATÓRIO ====================
async function exportBackup() {
  tacticalSound.radioChirp();
  try {
    const res = await fetch('/api/backup/export');
    const data = await res.json();
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const dateStr = new Date().toISOString().split('T')[0];
    a.href = url;
    a.download = `backup_qap_concursos_${dateStr}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    tacticalSound.missionComplete();
    showToast("Backup exportado com sucesso! Arquivo salvo no seu computador.");
  } catch (e) {
    console.error(e);
    showToast("Erro ao exportar backup.");
  }
}

function openBackupModal() {
  document.getElementById('modal-backup-import').classList.remove('hidden');
}

async function submitImportBackup() {
  const fileInput = document.getElementById('modal-backup-file');
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Selecione um arquivo de backup (.json) para importar.");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = async (e) => {
    try {
      const parsed = JSON.parse(e.target.result);
      const res = await fetch('/api/backup/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: parsed })
      });
      const data = await res.json();
      if (data.success) {
        tacticalSound.missionComplete();
        closeModal('modal-backup-import');
        showToast("Backup restaurado com sucesso! O sistema foi atualizado.");
        location.reload();
      } else {
        showToast(data.message || "Erro ao importar backup.");
      }
    } catch (err) {
      showToast("Arquivo de backup inválido ou corrompido.");
    }
  };

  reader.readAsText(file);
}

function printTacticalReport() {
  tacticalSound.beep(1100, 0.05);
  window.print();
}

// ==================== REDE LOCAL / ACESSO CELULAR ====================
async function openLanAccessModal() {
  tacticalSound.radioChirp();
  try {
    const res = await fetch('/api/network-info');
    const data = await res.json();
    const urlDisplay = document.getElementById('lan-url-display');
    const qrImg = document.getElementById('lan-qr-code');
    
    if (urlDisplay) urlDisplay.value = data.lan_url;
    if (qrImg) {
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(data.lan_url)}&color=050914&bgcolor=ffffff`;
    }
    document.getElementById('modal-lan-access')?.classList.remove('hidden');
  } catch (e) {
    console.error("Erro ao obter informações de rede:", e);
    const port = window.location.port || '8000';
    const fallbackUrl = `http://${window.location.hostname}:${port}`;
    const urlDisplay = document.getElementById('lan-url-display');
    if (urlDisplay) urlDisplay.value = fallbackUrl;
    document.getElementById('modal-lan-access')?.classList.remove('hidden');
  }
}

function copyLanUrl() {
  const urlDisplay = document.getElementById('lan-url-display');
  const btnText = document.getElementById('btn-copy-lan-text');
  if (urlDisplay) {
    urlDisplay.select();
    navigator.clipboard.writeText(urlDisplay.value).then(() => {
      tacticalSound.beep(1200, 0.05);
      if (btnText) {
        btnText.innerText = 'COPIADO!';
        setTimeout(() => { btnText.innerText = 'COPIAR'; }, 2000);
      }
    });
  }
}

// Close any open modal on escape key or clicking backdrop
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.add('hidden'));
  }
});

function closeModal(modalId) {
  document.getElementById(modalId)?.classList.add('hidden');
}

// ==================== GLOBAL SEARCH (COMMAND PALETTE CTRL + K) ====================
let searchDebounceTimer = null;
let currentSearchResults = [];
let currentSearchFilter = 'all';

function setupGlobalSearch() {
  window.addEventListener('keydown', (e) => {
    // Ctrl + K or Cmd + K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openGlobalSearchModal();
    }
  });
}

function openGlobalSearchModal() {
  tacticalSound.beep(950, 0.04);
  const modal = document.getElementById('modal-global-search');
  if (!modal) return;
  modal.classList.remove('hidden');
  const input = document.getElementById('global-search-input');
  if (input) {
    setTimeout(() => {
      input.focus();
      input.select();
    }, 50);
  }
}

function handleSearchBackdropClick(event) {
  if (event.target.id === 'modal-global-search') {
    closeModal('modal-global-search');
  }
}

function setSearchFilter(filterType) {
  currentSearchFilter = filterType;
  tacticalSound.beep(1100, 0.02);

  // Update pills style
  document.querySelectorAll('.search-filter-pill').forEach(btn => {
    if (btn.getAttribute('data-filter') === filterType) {
      btn.className = 'search-filter-pill px-2.5 py-0.5 rounded-full text-[11px] transition bg-blue-600 text-white font-semibold';
    } else {
      btn.className = 'search-filter-pill px-2.5 py-0.5 rounded-full text-[11px] transition bg-slate-800 hover:bg-slate-700 text-slate-300';
    }
  });

  renderSearchResults(currentSearchResults);
}

function onGlobalSearchInput(query) {
  clearTimeout(searchDebounceTimer);
  const q = query.trim();
  const container = document.getElementById('global-search-results');

  if (q.length < 2) {
    currentSearchResults = [];
    if (container) {
      container.innerHTML = `
        <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs">
          <i class="fa-solid fa-terminal text-2xl text-slate-600 mb-2"></i>
          <p>DIGITE PELO MENOS 2 CARACTERES PARA INICIAR A VARREDURA TÁTICA NO SISTEMA</p>
        </div>`;
    }
    return;
  }

  if (container) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-400 font-mono-tactical text-xs flex items-center justify-center space-x-2">
        <i class="fa-solid fa-circle-notch fa-spin text-blue-400 text-base"></i>
        <span>RASTREANDO BASE DE DADOS OPERACIONAL...</span>
      </div>`;
  }

  searchDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      if (!res.ok) throw new Error("Falha na busca");
      const data = await res.json();
      currentSearchResults = data.results || [];
      renderSearchResults(currentSearchResults, q);
    } catch (err) {
      console.error(err);
      if (container) {
        container.innerHTML = `
          <div class="p-6 text-center text-rose-400 font-mono-tactical text-xs">
            ERRO AO EFETUAR BUSCA NO SISTEMA.
          </div>`;
      }
    }
  }, 220);
}

function renderSearchResults(results, query = '') {
  const container = document.getElementById('global-search-results');
  if (!container) return;

  const filtered = currentSearchFilter === 'all' 
    ? results 
    : results.filter(r => r.type === currentSearchFilter);

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 font-mono-tactical text-xs">
        <i class="fa-solid fa-ban text-2xl text-slate-600 mb-2"></i>
        <p>NENHUM RESULTADO LOCALIZADO COM O FILTRO ATUAL${query ? ` PARA "${query.toUpperCase()}"` : ''}.</p>
      </div>`;
    return;
  }

  container.innerHTML = filtered.map(r => `
    <div onclick="selectSearchResult('${r.tab}', '${r.type}', ${r.ref_id || 0})" 
         class="p-3 rounded-xl bg-slate-900/70 hover:bg-slate-800/90 border border-slate-800/80 hover:border-blue-500/50 cursor-pointer transition flex items-start justify-between gap-3 group">
      <div class="flex items-start space-x-3">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" 
             style="background-color: ${r.color || '#3b82f6'}22; border: 1px solid ${r.color || '#3b82f6'}55">
          <i class="fa-solid ${r.icon || 'fa-crosshairs'} text-xs" style="color: ${r.color || '#3b82f6'}"></i>
        </div>
        <div>
          <div class="text-xs font-bold text-slate-100 group-hover:text-blue-400 transition flex items-center space-x-2">
            <span>${escapeHtml(r.title)}</span>
            <span class="text-[9px] font-mono-tactical px-1.5 py-0.2 rounded border bg-slate-950 text-slate-400 border-slate-800">${r.category}</span>
          </div>
          <div class="text-[11px] text-slate-400 font-mono-tactical mt-0.5">${r.subtitle}</div>
          ${r.detail ? `<div class="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed bg-slate-950/40 p-1.5 rounded border border-slate-800/50">${r.detail}</div>` : ''}
        </div>
      </div>
      <div class="text-right shrink-0">
        <span class="text-[10px] text-slate-500 group-hover:text-blue-400 font-mono-tactical flex items-center space-x-1">
          <span>IR</span>
          <i class="fa-solid fa-arrow-right text-[9px]"></i>
        </span>
      </div>
    </div>
  `).join('');
}

function selectSearchResult(tab, type, refId) {
  tacticalSound.beep(1200, 0.05);
  closeModal('modal-global-search');

  // Switch to destination tab
  switchTab(tab);

  // If topic: expand subject accordion if needed, and scroll to it with highlight
  if (type === 'topic' && refId) {
    setTimeout(() => {
      const topicEl = document.getElementById(`topic-item-${refId}`);
      if (topicEl) {
        topicEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        topicEl.classList.add('ring-2', 'ring-blue-500', 'bg-blue-950/40');
        setTimeout(() => {
          topicEl.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-950/40');
        }, 2500);
      } else {
        const subjCard = document.getElementById(`subject-card-${refId}`);
        if (subjCard) {
          subjCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
          toggleSubjectAccordion(refId);
        }
      }
    }, 200);
  } else if (type === 'error' && refId) {
    setTimeout(() => {
      const errEl = document.getElementById(`error-card-${refId}`);
      if (errEl) {
        errEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        errEl.classList.add('ring-2', 'ring-rose-500');
        setTimeout(() => {
          errEl.classList.remove('ring-2', 'ring-rose-500');
        }, 2500);
      }
    }, 200);
  }
}

// ==================== TACTICAL SIDEBAR COLLAPSIBLE CONTROLS ====================
function toggleSidebarCompact(forceState = null) {
  const sidebar = document.getElementById('tactical-sidebar');
  const mainCol = document.getElementById('main-content-column');
  const icon = document.getElementById('sidebar-toggle-icon');
  const btn = document.getElementById('btn-toggle-sidebar');
  if (!sidebar || !mainCol) return;

  const isCurrentlyCollapsed = sidebar.classList.contains('sidebar-collapsed');
  const shouldCollapse = forceState !== null ? forceState : !isCurrentlyCollapsed;

  if (shouldCollapse) {
    sidebar.classList.add('sidebar-collapsed');
    sidebar.classList.remove('lg:col-span-3');
    sidebar.classList.add('lg:col-span-1');
    mainCol.classList.remove('lg:col-span-9');
    mainCol.classList.add('lg:col-span-11');
    if (icon) {
      icon.className = 'fa-solid fa-angles-right text-xs';
    }
    if (btn) {
      btn.title = 'Expandir Menu Lateral (Mais Detalhes)';
    }
    try { localStorage.setItem('qap_sidebar_compact', 'true'); } catch (e) {}
  } else {
    sidebar.classList.remove('sidebar-collapsed');
    sidebar.classList.remove('lg:col-span-1');
    sidebar.classList.add('lg:col-span-3');
    mainCol.classList.remove('lg:col-span-11');
    mainCol.classList.add('lg:col-span-9');
    if (icon) {
      icon.className = 'fa-solid fa-angles-left text-xs';
    }
    if (btn) {
      btn.title = 'Recolher / Ocultar Menu Lateral (Mais Espaço)';
    }
    try { localStorage.setItem('qap_sidebar_compact', 'false'); } catch (e) {}
  }

  // Tactical subtle click audio feedback
  if (typeof tacticalSound !== 'undefined' && tacticalSound.beep) {
    tacticalSound.beep(900, 0.03);
  }

  // Trigger window resize so Chart.js recalculates layout properly
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
    if (state.charts?.activityChart) state.charts.activityChart.resize();
    if (state.charts?.subjectsChart) state.charts.subjectsChart.resize();
  }, 260);
}

function initSidebarState() {
  try {
    const saved = localStorage.getItem('qap_sidebar_compact');
    if (saved === 'true') {
      toggleSidebarCompact(true);
    }
  } catch (e) {
    console.warn('Sidebar state access denied/unavailable:', e);
  }
}
