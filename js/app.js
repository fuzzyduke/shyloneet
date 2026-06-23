// Early theme init to prevent flash
(function() {
  const savedTheme = localStorage.getItem('neetVaultTheme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
})();

// State Management
const STATE_KEY = 'neetVaultState';

function getState() {
  const defaultState = {
    papersProgress: {}, // { 'neet-2024': { status, physicsScore, chemistryScore, botanyScore, zoologyScore, biologyScore, totalScore, timeTaken, weakChapters: [], retestDate, notes } }
    mistakes: [] // [ { id, paperId, questionNumber, subject, chapter, mistakeType, priority, correctConcept, retestDate, status, date } ]
  };
  const stored = localStorage.getItem(STATE_KEY);
  return stored ? JSON.parse(stored) : defaultState;
}

function saveState(state) {
  localStorage.setItem(STATE_KEY, JSON.stringify(state));
}

// Data Fetching
async function fetchPapers() {
  try {
    const res = await fetch('data/papers.json');
    return await res.json();
  } catch (error) {
    console.error("Failed to load papers", error);
    return [];
  }
}

async function fetchChapters(subject = 'Physics', source = 'NCERT', classLevel = 12) {
  try {
    const apiBase = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : '';
    const url = `${apiBase}/api/chapters?subject=${subject}&source=${source}&class_level=${classLevel}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("API response not ok");
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch chapters from backend", error);
    return [];
  }
}

// Common UI Utils
function getStatusLabel(status) {
  const map = {
    'not-attempted': 'Not Attempted',
    'attempted': 'Attempted',
    'reviewed': 'Reviewed',
    'reattempt': 'Re-attempt Needed'
  };
  return map[status] || 'Not Attempted';
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('neetVaultTheme', newTheme);
  
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.innerText = newTheme === 'dark' ? '☀️' : '🌙';
  }
}

function renderNav() {
  const path = window.location.pathname;
  const page = path.split("/").pop();
  
  const nav = `
    <header>
      <a href="index.html" class="logo">📚 NEET Vault</a>
      <div style="display: flex; align-items: center; gap: 1rem;">
        <nav>
          <a href="index.html" class="${page === 'index.html' || page === '' ? 'active' : ''}">Dashboard</a>
          <a href="practice.html" class="${page === 'practice.html' ? 'active' : ''}">Practice</a>
          <a href="papers.html" class="${page === 'papers.html' ? 'active' : ''}">Papers</a>
          <a href="tracker.html" class="${page === 'tracker.html' ? 'active' : ''}">Tracker</a>
          <a href="mistakes.html" class="${page === 'mistakes.html' ? 'active' : ''}">Mistake Notebook</a>
          <a href="resources.html" class="${page === 'resources.html' ? 'active' : ''}">Resources</a>
        </nav>
        <button id="theme-toggle" class="btn btn-outline" style="padding: 0.5rem; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; cursor: pointer; border-color: var(--border-color); background: transparent;">🌙</button>
      </div>
    </header>
  `;
  document.getElementById('nav-placeholder').innerHTML = nav;
  
  const currentTheme = localStorage.getItem('neetVaultTheme') || 'light';
  document.documentElement.setAttribute('data-theme', currentTheme);
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.innerText = currentTheme === 'dark' ? '☀️' : '🌙';
    toggleBtn.addEventListener('click', toggleTheme);
  }
}

// Helper: Check if date is in the current week (next 7 days starting from today)
function isDueThisWeek(dateStr) {
  if (!dateStr) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateStr);
  target.setHours(0, 0, 0, 0);
  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 7);
  return target >= today && target <= nextWeek;
}

// 1. Dashboard (index.html)
async function initDashboard() {
  const state = getState();
  const papers = await fetchPapers();
  
  let totalAttempted = 0;
  let scoreSum = 0;
  let scoreCount = 0;
  let bestScore = 0;
  
  // Calculate statistics from papersProgress
  Object.values(state.papersProgress).forEach(p => {
    if (p.status && p.status !== 'not-attempted') {
      totalAttempted++;
    }
    const score = parseInt(p.totalScore);
    if (!isNaN(score) && score > 0) {
      scoreSum += score;
      scoreCount++;
      if (score > bestScore) {
        bestScore = score;
      }
    }
  });

  const avgScore = scoreCount > 0 ? Math.round(scoreSum / scoreCount) : '--';
  
  // Calculate weakest subject from mistakes
  const subjectMistakeCounts = {};
  state.mistakes.forEach(m => {
    if (m.status !== 'Fixed') {
      subjectMistakeCounts[m.subject] = (subjectMistakeCounts[m.subject] || 0) + 1;
    }
  });
  let weakestSubject = 'N/A';
  let maxMistakes = 0;
  Object.entries(subjectMistakeCounts).forEach(([sub, count]) => {
    if (count > maxMistakes) {
      maxMistakes = count;
      weakestSubject = sub;
    }
  });

  // Calculate next retest due (earliest future date across papers and mistakes)
  let nextRetestDate = null;
  const todayStr = new Date().toISOString().split('T')[0];
  
  Object.values(state.papersProgress).forEach(p => {
    if (p.retestDate && p.retestDate >= todayStr) {
      if (!nextRetestDate || p.retestDate < nextRetestDate) {
        nextRetestDate = p.retestDate;
      }
    }
  });
  state.mistakes.forEach(m => {
    if (m.status === 'Open' && m.retestDate && m.retestDate >= todayStr) {
      if (!nextRetestDate || m.retestDate < nextRetestDate) {
        nextRetestDate = m.retestDate;
      }
    }
  });

  // Calculate Weak Chapter Analytics
  const chapterFrequencies = {};
  let highPriorityCount = 0;
  let retestsThisWeek = 0;

  state.mistakes.forEach(m => {
    if (m.status === 'Open') {
      // Chapter frequency
      const chapKey = `${m.subject} - ${m.chapter}`;
      chapterFrequencies[chapKey] = (chapterFrequencies[chapKey] || 0) + 1;
      
      // High priority count
      if (m.priority === 'High') {
        highPriorityCount++;
      }
      
      // Retests this week
      if (isDueThisWeek(m.retestDate)) {
        retestsThisWeek++;
      }
    }
  });

  // Also include papers flagged for retest this week
  Object.values(state.papersProgress).forEach(p => {
    if (p.status === 'reattempt' && isDueThisWeek(p.retestDate)) {
      retestsThisWeek++;
    }
  });

  // Get top 5 weak chapters
  const topWeakChapters = Object.entries(chapterFrequencies)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  // Update DOM Elements
  document.getElementById('stat-attempted').innerText = `${totalAttempted} / ${papers.length}`;
  document.getElementById('stat-avg-score').innerText = avgScore;
  document.getElementById('stat-best-score').innerText = bestScore > 0 ? `${bestScore}/720` : '--';
  document.getElementById('stat-mistakes').innerText = state.mistakes.filter(m => m.status === 'Open').length;
  document.getElementById('stat-weakest-subject').innerText = weakestSubject;
  document.getElementById('stat-retest-due').innerText = nextRetestDate ? nextRetestDate : '--';

  // Render weak chapters
  const weakChaptersList = document.getElementById('analytics-weak-chapters');
  if (topWeakChapters.length > 0) {
    weakChaptersList.innerHTML = topWeakChapters.map(([chapter, count]) => `
      <li>
        <span>${chapter}</span>
        <span class="badge-count">${count} mistakes</span>
      </li>
    `).join('');
  } else {
    weakChaptersList.innerHTML = `<li style="justify-content: center; color: var(--text-muted);">No mistakes logged yet! Keep it up.</li>`;
  }

  // Render other cockpit cards
  document.getElementById('analytics-high-priority').innerText = highPriorityCount;
  document.getElementById('analytics-retests-week').innerText = retestsThisWeek;
  document.getElementById('analytics-weakest-subject').innerText = weakestSubject;

  // Primary CTA Setup: Start Latest NEET Paper
  // Find the latest paper in papers array (by year) that is not completed
  const startBtn = document.getElementById('primary-cta-start');
  if (startBtn && papers.length > 0) {
    // Sort papers descending by year
    const sorted = [...papers].sort((a, b) => b.year - a.year);
    const latestUnattempted = sorted.find(p => {
      const prog = state.papersProgress[p.id];
      return !prog || prog.status === 'not-attempted' || prog.status === 'reattempt';
    }) || sorted[0]; // fallback to latest paper

    startBtn.href = `paper-detail.html?id=${latestUnattempted.id}`;
    startBtn.innerHTML = `Start Latest Paper (${latestUnattempted.title}) &rarr;`;
  }
}

// 2. Papers List (papers.html)
async function initPapers() {
  const state = getState();
  const papers = await fetchPapers();
  const container = document.getElementById('papers-container');
  
  if (papers.length === 0) {
    container.innerHTML = "<p>No papers defined yet.</p>";
    return;
  }

  container.innerHTML = papers.map(paper => {
    const progress = state.papersProgress[paper.id] || { 
      status: 'not-attempted', 
      totalScore: '', 
      retestDate: '' 
    };
    
    // Count mistakes for this specific paper
    const paperMistakes = state.mistakes.filter(m => m.paperId === paper.id && m.status === 'Open').length;
    
    if (paper.id === 'neet-2025-045') {
      const hasAttempt = localStorage.getItem('shylo_neet_2025_045_attempt');
      let attemptState = hasAttempt ? JSON.parse(hasAttempt) : null;
      const isSubmitted = attemptState && attemptState.submitted;
      
      return `
        <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; min-height: 380px; border: 1px solid var(--primary);">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
              <h3>${paper.title}</h3>
              <span class="badge badge-${progress.status}">
                ${getStatusLabel(progress.status)}
              </span>
            </div>
            <p class="text-muted" style="font-size: 0.9rem; margin-bottom: 1rem;">
              Code: <strong>45</strong> | Type: <strong>${paper.type}</strong>
            </p>
            
            <ul style="list-style: none; margin-bottom: 1.5rem; font-size: 0.95rem; display: flex; flex-direction: column; gap: 0.4rem;">
              <li>📚 <strong>Subjects:</strong> Physics + Chemistry + Biology</li>
              <li>❓ <strong>Questions:</strong> 180</li>
              <li>💯 <strong>Marks:</strong> 720</li>
              <li>⏱️ <strong>Duration:</strong> 3h 20m</li>
              <li>🎯 <strong>Your Score:</strong> ${progress.totalScore ? `<strong>${progress.totalScore}</strong>/720` : '<span style="color: var(--text-muted)">N/A</span>'}</li>
              <li>⚠️ <strong>Mistakes Logged:</strong> <span class="${paperMistakes > 0 ? 'badge priority-high' : ''}">${paperMistakes} active</span></li>
            </ul>
          </div>
          
          <div style="display: flex; flex-direction: column; gap: 0.5rem;">
            <div style="display: flex; gap: 0.5rem;">
              <a href="test.html?paper=${paper.id}" class="btn btn-primary btn-sm" style="flex: 1;">🚀 Start Test</a>
              <a href="test.html?paper=${paper.id}" class="btn btn-outline btn-sm" style="flex: 1; ${attemptState ? '' : 'opacity: 0.5; pointer-events: none;'}">🔁 Resume</a>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <a href="test.html?paper=${paper.id}&result=true" class="btn btn-outline btn-sm" style="flex: 1; ${isSubmitted ? '' : 'opacity: 0.5; pointer-events: none;'}">📊 View Result</a>
              <a href="${paper.paperUrl}" target="_blank" class="btn btn-outline btn-sm" style="flex: 1;">📄 Open PDF</a>
            </div>
          </div>
        </div>
      `;
    }
    
    return `
      <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; min-height: 380px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
            <h3>${paper.title}</h3>
            <span class="badge badge-${progress.status}">
              ${getStatusLabel(progress.status)}
            </span>
          </div>
          <p class="text-muted" style="font-size: 0.9rem; margin-bottom: 1rem;">
            Year: <strong>${paper.year}</strong> | Type: <strong>${paper.type}</strong>
          </p>
          
          <ul style="list-style: none; margin-bottom: 1.5rem; font-size: 0.95rem; display: flex; flex-direction: column; gap: 0.4rem;">
            <li>📚 <strong>Subjects:</strong> Physics, Chemistry, Botany, Zoology</li>
            <li>⏱️ <strong>Duration:</strong> 3h 20m (200m)</li>
            <li>💯 <strong>Total Marks:</strong> 720</li>
            <li>🎯 <strong>Score:</strong> ${progress.totalScore ? `<strong>${progress.totalScore}</strong>/720` : '<span style="color: var(--text-muted)">N/A</span>'}</li>
            <li>⚠️ <strong>Mistakes Logged:</strong> <span class="${paperMistakes > 0 ? 'badge priority-high' : ''}">${paperMistakes} active</span></li>
            <li>📅 <strong>Retest Date:</strong> ${progress.retestDate ? `<strong>${progress.retestDate}</strong>` : '--'}</li>
          </ul>
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 0.5rem;">
          <div style="display: flex; gap: 0.5rem;">
            <a href="${paper.paperUrl}" target="_blank" class="btn btn-outline btn-sm" style="flex: 1;">📄 Q. Paper</a>
            <a href="${paper.answerKeyUrl}" target="_blank" class="btn btn-outline btn-sm" style="flex: 1;">🔑 Ans. Key</a>
          </div>
          <div style="display: flex; gap: 0.5rem;">
            <a href="paper-detail.html?id=${paper.id}" class="btn btn-primary btn-sm" style="flex: 1;">📝 Log Score</a>
            <button onclick="quickReattempt('${paper.id}')" class="btn btn-outline btn-sm" style="flex: 1;">🔁 Retest</button>
          </div>
          <a href="mistakes.html?paperId=${paper.id}" class="btn btn-outline btn-sm" style="width: 100%;">⚠️ Review Mistakes</a>
        </div>
      </div>
    `;
  }).join('');
}

function quickReattempt(paperId) {
  const state = getState();
  if (!state.papersProgress[paperId]) {
    state.papersProgress[paperId] = {};
  }
  state.papersProgress[paperId].status = 'reattempt';
  
  // Set a default retest date 3 days from now
  const retest = new Date();
  retest.setDate(retest.getDate() + 3);
  state.papersProgress[paperId].retestDate = retest.toISOString().split('T')[0];
  
  saveState(state);
  initPapers();
}

// 3. Paper Detail (paper-detail.html)
let timerInterval;
let secondsElapsed = 0;

async function initPaperDetail() {
  const params = new URLSearchParams(window.location.search);
  const paperId = params.get('id');
  if (!paperId) {
    window.location.href = 'papers.html';
    return;
  }

  const papers = await fetchPapers();
  const paper = papers.find(p => p.id === paperId);
  if (!paper) {
    window.location.href = 'papers.html';
    return;
  }

  document.getElementById('paper-title').innerText = paper.title;
  document.getElementById('qp-link').href = paper.paperUrl;
  document.getElementById('ak-link').href = paper.answerKeyUrl;
  
  // Pre-fill log mistake link shortcut
  const shortcutLink = document.getElementById('log-mistake-shortcut');
  if (shortcutLink) {
    shortcutLink.href = `mistakes.html?paperId=${paper.id}`;
  }

  const state = getState();
  const progress = state.papersProgress[paperId] || {
    status: 'not-attempted',
    physicsScore: '',
    chemistryScore: '',
    botanyScore: '',
    zoologyScore: '',
    biologyScore: '',
    totalScore: '',
    timeTaken: '',
    weakChapters: [],
    retestDate: '',
    notes: '',
    duration: 0
  };

  // Pre-fill Form Fields
  document.getElementById('status-select').value = progress.status || 'not-attempted';
  document.getElementById('score-physics').value = progress.physicsScore || '';
  document.getElementById('score-chemistry').value = progress.chemistryScore || '';
  document.getElementById('score-botany').value = progress.botanyScore || '';
  document.getElementById('score-zoology').value = progress.zoologyScore || '';
  document.getElementById('score-biology').value = progress.biologyScore || '';
  document.getElementById('score-total').value = progress.totalScore || '';
  document.getElementById('retest-date').value = progress.retestDate || '';
  document.getElementById('notes-input').value = progress.notes || '';
  
  // Convert array back to comma-separated string for editing
  document.getElementById('weak-chapters-input').value = progress.weakChapters ? progress.weakChapters.join(', ') : '';

  secondsElapsed = progress.duration || 0;
  updateTimerDisplay();

  // Set up listeners for live score auto-calculations
  const inputs = ['score-physics', 'score-chemistry', 'score-botany', 'score-zoology'];
  inputs.forEach(id => {
    document.getElementById(id).addEventListener('input', calculateScores);
  });

  // Form Save Action
  document.getElementById('save-btn').addEventListener('click', () => {
    const p = parseInt(document.getElementById('score-physics').value) || 0;
    const c = parseInt(document.getElementById('score-chemistry').value) || 0;
    const b = parseInt(document.getElementById('score-botany').value) || 0;
    const z = parseInt(document.getElementById('score-zoology').value) || 0;
    const bioTotal = b + z;
    const grandTotal = p + c + bioTotal;

    const weakChapsRaw = document.getElementById('weak-chapters-input').value;
    const weakChaptersArray = weakChapsRaw.split(',').map(s => s.trim()).filter(s => s.length > 0);

    // Calculate time taken from seconds elapsed if they used the timer
    let timeDisplay = '';
    if (secondsElapsed > 0) {
      const hrs = Math.floor(secondsElapsed / 3600);
      const mins = Math.floor((secondsElapsed % 3600) / 60);
      timeDisplay = `${hrs}h ${mins}m`;
    }

    state.papersProgress[paperId] = {
      status: document.getElementById('status-select').value,
      physicsScore: p || '',
      chemistryScore: c || '',
      botanyScore: b || '',
      zoologyScore: z || '',
      biologyScore: bioTotal || '',
      totalScore: grandTotal || '',
      timeTaken: timeDisplay || progress.timeTaken || '',
      weakChapters: weakChaptersArray,
      retestDate: document.getElementById('retest-date').value,
      notes: document.getElementById('notes-input').value,
      duration: secondsElapsed
    };

    saveState(state);
    showCustomAlert('Progress Saved', 'Practice session progress saved successfully!');
  });
}

function calculateScores() {
  const p = parseInt(document.getElementById('score-physics').value) || 0;
  const c = parseInt(document.getElementById('score-chemistry').value) || 0;
  const b = parseInt(document.getElementById('score-botany').value) || 0;
  const z = parseInt(document.getElementById('score-zoology').value) || 0;

  const bioTotal = b + z;
  const grandTotal = p + c + bioTotal;

  document.getElementById('score-biology').value = bioTotal || '';
  document.getElementById('score-total').value = grandTotal || '';
}

function updateTimerDisplay() {
  const h = Math.floor(secondsElapsed / 3600).toString().padStart(2, '0');
  const m = Math.floor((secondsElapsed % 3600) / 60).toString().padStart(2, '0');
  const s = (secondsElapsed % 60).toString().padStart(2, '0');
  document.getElementById('timer-display').innerText = `${h}:${m}:${s}`;
}

function startTimer() {
  if (timerInterval) return;
  timerInterval = setInterval(() => {
    secondsElapsed++;
    updateTimerDisplay();
  }, 1000);
}

function pauseTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

function resetTimer() {
  pauseTimer();
  secondsElapsed = 0;
  updateTimerDisplay();
}

// 4. Mistake Notebook (mistakes.html)
async function initMistakes() {
  const papers = await fetchPapers();
  const paperSelect = document.getElementById('m-paper');
  paperSelect.innerHTML = papers.map(p => `<option value="${p.id}">${p.title}</option>`).join('');

  // Populate Filter Selectors
  const filterPaper = document.getElementById('filter-paper');
  filterPaper.innerHTML = '<option value="all">All Papers</option>' + 
    papers.map(p => `<option value="${p.id}">${p.title}</option>`).join('');

  // Pre-fill form and filter if url contains paperId
  const params = new URLSearchParams(window.location.search);
  const urlPaperId = params.get('paperId');
  if (urlPaperId) {
    paperSelect.value = urlPaperId;
    filterPaper.value = urlPaperId;
  }

  // Register form submission
  document.getElementById('mistake-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const state = getState();
    const newMistake = {
      id: 'mistake-' + Date.now(),
      paperId: document.getElementById('m-paper').value,
      questionNumber: document.getElementById('m-qnumber').value,
      subject: document.getElementById('m-subject').value,
      chapter: document.getElementById('m-chapter').value,
      mistakeType: document.getElementById('m-type').value,
      priority: document.getElementById('m-priority').value,
      correctConcept: document.getElementById('m-concept').value,
      retestDate: document.getElementById('m-retest').value,
      status: 'Open',
      date: new Date().toISOString().split('T')[0]
    };
    state.mistakes.push(newMistake);
    saveState(state);
    e.target.reset();
    
    // reset selection if needed
    if (urlPaperId) {
      document.getElementById('m-paper').value = urlPaperId;
    }
    
    renderMistakesTable();
  });

  // Attach filter event listeners
  const filterIds = ['filter-subject', 'filter-paper', 'filter-priority', 'filter-status', 'filter-retest'];
  filterIds.forEach(id => {
    document.getElementById(id).addEventListener('change', renderMistakesTable);
  });

  renderMistakesTable();
}

async function renderMistakesTable() {
  const state = getState();
  const papers = await fetchPapers();
  const tbody = document.getElementById('mistakes-tbody');
  
  // Retrieve filters
  const filterSub = document.getElementById('filter-subject').value;
  const filterPap = document.getElementById('filter-paper').value;
  const filterPrio = document.getElementById('filter-priority').value;
  const filterStat = document.getElementById('filter-status').value;
  const filterRetest = document.getElementById('filter-retest').value;

  // Filter mistakes list
  const filtered = state.mistakes.filter(m => {
    if (filterSub !== 'all' && m.subject !== filterSub) return false;
    if (filterPap !== 'all' && m.paperId !== filterPap) return false;
    if (filterPrio !== 'all' && m.priority !== filterPrio) return false;
    if (filterStat !== 'all' && m.status !== filterStat) return false;
    
    // Retest filters
    if (filterRetest === 'due-week' && !isDueThisWeek(m.retestDate)) return false;
    if (filterRetest === 'past-due') {
      const todayStr = new Date().toISOString().split('T')[0];
      if (!m.retestDate || m.retestDate >= todayStr || m.status === 'Fixed') return false;
    }
    
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No matching mistakes logged.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(m => {
    const paper = papers.find(p => p.id === m.paperId) || { title: 'Unknown Paper' };
    
    return `
      <tr>
        <td><strong>Q${m.questionNumber || '--'}</strong><br><small style="color: var(--text-muted)">${paper.title}</small></td>
        <td><strong>${m.subject}</strong><br><span style="font-size: 0.85rem">${m.chapter}</span></td>
        <td><span style="font-size: 0.9rem">${m.mistakeType}</span></td>
        <td><span class="priority-badge priority-${m.priority.toLowerCase()}">${m.priority}</span></td>
        <td style="max-width: 250px; font-size: 0.9rem;">${m.correctConcept}</td>
        <td>${m.retestDate ? `<code>${m.retestDate}</code>` : '--'}</td>
        <td>
          <select onchange="updateMistakeStatus('${m.id}', this.value)" class="badge status-${m.status.toLowerCase()}" style="padding: 0.2rem 0.5rem; margin-bottom: 0; font-size: 0.8rem; width: auto; font-weight: 700;">
            <option value="Open" ${m.status === 'Open' ? 'selected' : ''}>Open</option>
            <option value="Revised" ${m.status === 'Revised' ? 'selected' : ''}>Revised</option>
            <option value="Fixed" ${m.status === 'Fixed' ? 'selected' : ''}>Fixed</option>
          </select>
        </td>
        <td>
          <button onclick="deleteMistake('${m.id}')" class="btn btn-outline btn-sm" style="border-color: #fca5a5; color: #dc2626; padding: 0.25rem 0.5rem;">Delete</button>
        </td>
      </tr>
    `;
  }).join('');
}

function updateMistakeStatus(mistakeId, newStatus) {
  const state = getState();
  const mistake = state.mistakes.find(m => m.id === mistakeId);
  if (mistake) {
    mistake.status = newStatus;
    saveState(state);
    renderMistakesTable();
  }
}

function deleteMistake(mistakeId) {
  showCustomConfirm('Delete Mistake?', 'Are you sure you want to delete this mistake from your notebook?', () => {
    const state = getState();
    state.mistakes = state.mistakes.filter(m => m.id !== mistakeId);
    saveState(state);
    renderMistakesTable();
  });
}

// 5. Tracker (tracker.html)
async function initTracker() {
  const state = getState();
  const papers = await fetchPapers();
  
  const scores = papers.map(p => {
    const prog = state.papersProgress[p.id];
    const score = prog && prog.totalScore ? parseInt(prog.totalScore) : 0;
    return { title: p.title, score };
  }).filter(s => s.score > 0);

  const container = document.getElementById('tracker-container');
  
  if (scores.length === 0) {
    container.innerHTML = "<p style='text-align: center; color: var(--text-muted); padding: 2rem;'>No scores recorded yet. Attempt a paper and log your score!</p>";
    return;
  }

  const maxScore = 720;
  container.innerHTML = `
    <h2 style="margin-bottom: 1.5rem;">Practice Trend</h2>
    ${scores.map(s => {
      const heightPercentage = (s.score / maxScore) * 100;
      let barColor = 'var(--secondary)'; // poor
      if (s.score >= 600) barColor = 'var(--success)'; // excellent
      else if (s.score >= 500) barColor = 'var(--primary)'; // good
      else if (s.score >= 400) barColor = 'var(--accent)'; // average

      return `
        <div style="margin-bottom: 1.5rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <strong>${s.title}</strong>
            <span style="font-weight: 700; color: ${barColor}">${s.score} / 720</span>
          </div>
          <div style="width: 100%; height: 24px; background: var(--primary-light); border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color);">
            <div style="width: ${heightPercentage}%; height: 100%; background: ${barColor}; border-radius: 12px; transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: inset 0 -2px 6px rgba(0,0,0,0.1);"></div>
          </div>
        </div>
      `;
    }).join('')}
  `;
}

// Custom Dialog System
function showCustomConfirm(title, message, onConfirm) {
  let modal = document.getElementById('custom-confirm-modal');
  if (!modal) {
    const modalHTML = `
      <div id="custom-confirm-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="max-width: 450px; text-align: center;">
          <h3 id="custom-confirm-title" style="margin-bottom: 1rem;">Confirmation</h3>
          <p id="custom-confirm-message" style="margin-bottom: 1.5rem; color: var(--text-muted); font-size: 0.95rem;"></p>
          <div style="display: flex; gap: 1rem; justify-content: center;">
            <button id="custom-confirm-yes" class="btn btn-primary" style="flex: 1;">Yes, Proceed</button>
            <button id="custom-confirm-no" class="btn btn-outline" style="flex: 1;">Cancel</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    modal = document.getElementById('custom-confirm-modal');
    
    document.getElementById('custom-confirm-no').addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }
  
  document.getElementById('custom-confirm-title').innerText = title;
  document.getElementById('custom-confirm-message').innerText = message;
  modal.style.display = 'flex';
  
  const yesBtn = document.getElementById('custom-confirm-yes');
  const newYesBtn = yesBtn.cloneNode(true);
  yesBtn.parentNode.replaceChild(newYesBtn, yesBtn);
  
  newYesBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    if (onConfirm) onConfirm();
  });
}

function showCustomAlert(title, message) {
  let modal = document.getElementById('custom-alert-modal');
  if (!modal) {
    const modalHTML = `
      <div id="custom-alert-modal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="max-width: 400px; text-align: center;">
          <h3 id="custom-alert-title" style="margin-bottom: 1rem;">Notice</h3>
          <p id="custom-alert-message" style="margin-bottom: 1.5rem; color: var(--text-muted); font-size: 0.95rem;"></p>
          <button id="custom-alert-ok" class="btn btn-primary" style="width: 100%;">OK</button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    modal = document.getElementById('custom-alert-modal');
    
    document.getElementById('custom-alert-ok').addEventListener('click', () => {
      modal.style.display = 'none';
    });
  }
  
  document.getElementById('custom-alert-title').innerText = title;
  document.getElementById('custom-alert-message').innerText = message;
  modal.style.display = 'flex';
}

// 6. Practice UI (practice.html)
async function initPractice() {
  const container = document.getElementById('chapter-list-container');
  const subjectSelect = document.getElementById('subject-select');
  const generateBtn = document.getElementById('generate-test-btn');
  const selectAllBtn = document.getElementById('select-all-btn');

  const loadChapters = async () => {
    container.innerHTML = '<p class="text-muted" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">Loading chapters from database...</p>';
    const subject = subjectSelect.value;
    const chapters = await fetchChapters(subject);
    
    if (chapters.length === 0) {
      container.innerHTML = `<p class="text-muted" style="grid-column: 1 / -1; text-align: center; padding: 2rem;">No chapters found for ${subject} in the database. Please ensure backend is running and data is ingested.</p>`;
      return;
    }

    container.innerHTML = chapters.map(c => `
      <label class="chapter-item">
        <input type="checkbox" class="chapter-checkbox" value="${c.id}" />
        <div class="chapter-item-content">
          <div class="chapter-item-title">Chapter ${c.chapter_number}: ${c.chapter_name}</div>
          <div class="chapter-item-meta">${c.source} Class ${c.class_level}</div>
        </div>
      </label>
    `).join('');
  };

  await loadChapters();

  subjectSelect.addEventListener('change', loadChapters);

  let allSelected = false;
  selectAllBtn.addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('.chapter-checkbox');
    allSelected = !allSelected;
    checkboxes.forEach(cb => cb.checked = allSelected);
    selectAllBtn.innerText = allSelected ? 'Deselect All' : 'Select All';
  });

  generateBtn.addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('.chapter-checkbox:checked');
    if (checkboxes.length === 0) {
      showCustomAlert('Selection Required', 'Please select at least one chapter to generate a custom test.');
      return;
    }
    // Block the test generation because no questions are mapped yet
    showCustomAlert('Questions Pending', 'No questions are currently mapped to these chapters. Awaiting previous-year paper ingestion.');
  });
}
