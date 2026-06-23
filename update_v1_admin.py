import re

with open("v1_admin.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add new styles
new_styles = """
        .triage-section {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 2rem;
            box-shadow: var(--shadow-md);
            margin-top: 2rem;
        }

        .upload-zone {
            border: 2px dashed var(--primary);
            border-radius: 16px;
            padding: 3rem 2rem;
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            margin-bottom: 2rem;
            background: rgba(255,255,255,0.02);
        }

        .upload-zone:hover {
            background: rgba(255,255,255,0.05);
            transform: scale(1.01);
        }

        .triage-stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .triage-stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }

        .triage-stat-val {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.2rem;
        }

        .triage-stat-label {
            font-size: 0.8rem;
            color: var(--text-muted);
        }
        
        /* Full width container for review table */
        .full-width-container {
            width: 100%;
            overflow-x: auto;
            margin-top: 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }
        
        .full-width-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 1200px;
        }
        
        .full-width-table th, .full-width-table td {
            padding: 0.75rem;
            border-bottom: 1px solid var(--border-color);
            text-align: left;
        }
        
        .full-width-table th {
            background: var(--card-bg);
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        /* Sticky first columns */
        .full-width-table th:nth-child(1), .full-width-table td:nth-child(1),
        .full-width-table th:nth-child(2), .full-width-table td:nth-child(2) {
            position: sticky;
            left: 0;
            background: var(--bg-color);
            z-index: 5;
        }
        .full-width-table th:nth-child(1), .full-width-table th:nth-child(2) {
            z-index: 15;
            background: var(--card-bg);
        }
        
        .filter-bar {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.02);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        .filter-bar select, .filter-bar input {
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-color);
            color: var(--text-color);
        }
"""

html = re.sub(r'</style>', new_styles + '\n    </style>', html)

# 2. Replace the layout grid
body_grid = """
        <div class="admin-header-desc" style="margin-top: 2rem;">
            <h2>A. Reference Material Library</h2>
            <p class="text-muted">Manage reference databases (NCERT Textbooks).</p>
        </div>

        <div class="subject-grid" id="subject-grid">
            <div class="card subject-card" onclick="selectSubject('Physics')">
                <div class="subject-card-header">
                    <span class="subject-title">Physics</span>
                    <div class="badge-list"><span class="badge badge-ingested">Ingested</span></div>
                </div>
                <div class="stat-line"><span>Chapters:</span><span id="phys-chapters-count">Loading...</span></div>
            </div>
            <div class="card subject-card" onclick="selectSubject('Chemistry')">
                <div class="subject-card-header">
                    <span class="subject-title">Chemistry</span>
                    <div class="badge-list"><span class="badge badge-placeholder">Pending</span></div>
                </div>
            </div>
            <div class="card subject-card" onclick="selectSubject('Biology')">
                <div class="subject-card-header">
                    <span class="subject-title">Biology</span>
                    <div class="badge-list"><span class="badge badge-placeholder">Pending</span></div>
                </div>
            </div>
        </div>

        <div class="admin-header-desc" style="margin-top: 3rem;">
            <h2>B. Question Paper Library</h2>
            <p class="text-muted">Manage full 180-question NEET papers, mock tests, and JSON imports.</p>
        </div>
        
        <div class="subject-grid">
            <div class="card subject-card physics-active" onclick="selectSubject('PaperLibrary')">
                <div class="subject-card-header">
                    <span class="subject-title">Question Papers</span>
                    <div class="badge-list"><span class="badge badge-ingested" style="background-color: var(--accent-light); color: var(--accent);">Active</span></div>
                </div>
                <div class="stat-line"><span>Total Papers:</span><span id="total-papers-count">Loading...</span></div>
                <div class="subject-card-note">View, manage, and import question papers.</div>
            </div>
        </div>
"""

html = re.sub(r'<!-- Subject Overview Cards -->.*?<!-- Details Panel \(Physics\) -->', body_grid + '\n\n        <!-- Details Panel (Physics) -->', html, flags=re.DOTALL)

# 3. Add PaperLibrary Detail Panel and update Triage panel
panels = """
        <!-- Details Panel (PaperLibrary) -->
        <div id="detail-panel-PaperLibrary" class="detail-panel" style="display: block;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h2>📚 Paper Management</h2>
                <button class="btn btn-primary" onclick="selectSubject('Triage')">Import New Paper JSON</button>
            </div>
            
            <div class="filter-bar">
                <select id="filter-year"><option value="">All Years</option><option value="2025">2025</option><option value="2024">2024</option></select>
                <select id="filter-subject"><option value="">All Subjects</option><option value="Full Paper">Full Paper</option></select>
                <select id="filter-status"><option value="">All Statuses</option><option value="needs_review">Needs Review</option><option value="approved">Approved</option></select>
                <button class="btn btn-outline btn-sm" onclick="fetchPapers()">Apply Filters</button>
            </div>
            
            <div class="full-width-container">
                <table class="full-width-table">
                    <thead>
                        <tr>
                            <th>Title / Source</th>
                            <th>Year</th>
                            <th>Set Code</th>
                            <th>Type</th>
                            <th>Subjects</th>
                            <th>Total Expected</th>
                            <th>Parsed</th>
                            <th>Needs Review</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="papers-tbody">
                        <tr><td colspan="10" style="text-align: center;">Loading papers...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Details Panel (Triage) -->
        <div id="detail-panel-Triage" class="detail-panel">
            <div class="triage-section" style="max-width: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h2>Import Paper JSON</h2>
                    <button class="btn btn-outline" onclick="selectSubject('PaperLibrary')">Cancel</button>
                </div>

                <div class="upload-zone" id="upload-zone">
                    <span style="font-size: 3rem; display: block; margin-bottom: 1rem;">📁</span>
                    <h3 id="upload-prompt">Upload paper_triage.json</h3>
                    <p class="text-muted" style="margin-top: 0.5rem; font-size: 0.85rem;">Must contain 180 questions with paper metadata</p>
                    <input type="file" id="json-file-input" accept="application/json" style="display: none;" />
                </div>

                <div id="triage-loading" style="display: none; text-align: center; padding: 2rem;">
                    <span style="font-size: 1.5rem; display: inline-block; animation: spin 2s linear infinite; margin-bottom: 1rem;">🔄</span>
                    <h3>Processing Full Paper...</h3>
                </div>

                <div id="triage-result-container" style="display: none;">
                    <h3>Paper Summary</h3>
                    <div class="triage-stats-grid">
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-expected">180</div><div class="triage-stat-label">Expected</div></div>
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-parsed">0</div><div class="triage-stat-label">Parsed</div></div>
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-missing">0</div><div class="triage-stat-label">Missing</div></div>
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-complete">0</div><div class="triage-stat-label">Complete Options</div></div>
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-answers">0</div><div class="triage-stat-label">Answers Found</div></div>
                        <div class="triage-stat-card"><div class="triage-stat-val" id="stat-review" style="color: #ef4444;">0</div><div class="triage-stat-label">Needs Review</div></div>
                    </div>
                    
                    <h3>Subject Breakdown</h3>
                    <table class="chapter-table" style="margin-bottom: 2rem;">
                        <thead><tr><th>Subject</th><th>Expected</th><th>Parsed</th><th>Missing Options</th><th>Answers Found</th><th>Needs Review</th></tr></thead>
                        <tbody id="subject-breakdown-tbody"></tbody>
                    </table>

                    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                        <h3>Parsed Questions Preview</h3>
                        <div class="filter-bar" style="margin-bottom: 0;">
                            <select id="q-filter-subject" onchange="renderTriagePreview()"><option value="">All Subjects</option><option value="Physics">Physics</option><option value="Chemistry">Chemistry</option><option value="Biology">Biology</option></select>
                            <select id="q-filter-status" onchange="renderTriagePreview()"><option value="">All Status</option><option value="needs_review">Needs Review</option><option value="approved">Approved</option></select>
                        </div>
                    </div>
                    
                    <div class="full-width-container" style="max-height: 600px; overflow-y: auto;">
                        <table class="full-width-table">
                            <thead>
                                <tr>
                                    <th>Q# (Global)</th>
                                    <th>Subject</th>
                                    <th>Q# (Local)</th>
                                    <th>Question Preview</th>
                                    <th>Options</th>
                                    <th>Answer</th>
                                    <th>Assets</th>
                                    <th>Page</th>
                                    <th>Conf.</th>
                                    <th>Status</th>
                                    <th>Review Reasons</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="triage-preview-tbody"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
"""

html = re.sub(r'<!-- Details Panel \(Triage\) -->.*?(?=<!-- Details Modal -->)', panels + '\n\n        ', html, flags=re.DOTALL)

# 4. Update the Javascript logic
js_updates = """
        // Parse AG Triage JSON output
        function handleJSONUpload(file) {
            document.getElementById('upload-zone').style.display = 'none';
            document.getElementById('triage-loading').style.display = 'block';
            document.getElementById('triage-result-container').style.display = 'none';

            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = JSON.parse(e.target.result);
                    // Support both old array-based and new object-based JSON
                    if (Array.isArray(data.questions)) {
                        currentMetadata = data.paper || data.metadata || {
                            title: "Imported Paper",
                            exam: "NEET",
                            subject: "Full Paper",
                            year: 2024,
                            source: "AG"
                        };
                        parsedQuestionsList = data.questions;
                    } else {
                        parsedQuestionsList = data;
                    }
                    
                    // Render UI
                    renderTriagePreview(data);
                } catch (err) {
                    console.error("JSON parse failed:", err);
                    alert("Invalid JSON file. Please ensure it is a valid paper_triage.json.");
                    document.getElementById('upload-zone').style.display = 'block';
                    document.getElementById('triage-loading').style.display = 'none';
                }
            };
            reader.readAsText(file);
        }

        // Render preview table
        function renderTriagePreview(data) {
            const subjFilter = document.getElementById('q-filter-subject')?.value || '';
            const statFilter = document.getElementById('q-filter-status')?.value || '';
        
            let expected = currentMetadata.expected_question_count || 180;
            let parsed = parsedQuestionsList.length;
            let missing = expected - parsed;
            let completeOpts = 0;
            let answersFound = 0;
            let needsRev = 0;
            
            let subStats = {
                'Physics': {exp: 45, par: 0, missO: 0, ans: 0, rev: 0},
                'Chemistry': {exp: 45, par: 0, missO: 0, ans: 0, rev: 0},
                'Biology': {exp: 90, par: 0, missO: 0, ans: 0, rev: 0}
            };

            parsedQuestionsList.forEach(q => {
                const optCount = q.options ? Object.values(q.options).filter(Boolean).length : 0;
                if (optCount === 4) completeOpts++;
                if (q.correct_option || q.answer) answersFound++;
                if (q.needs_review && !q.approved) needsRev++;
                
                const s = q.subject || 'Unknown';
                if (subStats[s]) {
                    subStats[s].par++;
                    if (optCount < 4) subStats[s].missO++;
                    if (q.correct_option || q.answer) subStats[s].ans++;
                    if (q.needs_review && !q.approved) subStats[s].rev++;
                }
            });

            document.getElementById('stat-expected').innerText = expected;
            document.getElementById('stat-parsed').innerText = parsed;
            document.getElementById('stat-missing').innerText = missing > 0 ? missing : 0;
            document.getElementById('stat-complete').innerText = completeOpts;
            document.getElementById('stat-answers').innerText = answersFound;
            document.getElementById('stat-review').innerText = needsRev;

            const stbody = document.getElementById('subject-breakdown-tbody');
            if (stbody) {
                stbody.innerHTML = Object.keys(subStats).map(s => `
                    <tr>
                        <td><strong>${s}</strong></td>
                        <td>${subStats[s].exp}</td>
                        <td>${subStats[s].par}</td>
                        <td style="color: ${subStats[s].missO > 0 ? '#ef4444' : 'inherit'}">${subStats[s].missO}</td>
                        <td>${subStats[s].ans}</td>
                        <td style="color: ${subStats[s].rev > 0 ? '#ef4444' : 'inherit'}">${subStats[s].rev}</td>
                    </tr>
                `).join('');
            }

            // Render questions table
            const tbody = document.getElementById('triage-preview-tbody');
            if (tbody) {
                const filtered = parsedQuestionsList.filter(q => {
                    if (subjFilter && q.subject !== subjFilter) return false;
                    const isApproved = q.approved === true;
                    if (statFilter === 'approved' && !isApproved) return false;
                    if (statFilter === 'needs_review' && isApproved) return false;
                    if (statFilter === 'needs_review' && !q.needs_review) return false;
                    return true;
                });
                
                tbody.innerHTML = filtered.map(q => {
                    const isApproved = q.approved === true;
                    const statusText = isApproved ? 'Approved' : (q.needs_review ? 'Needs Review' : 'Pending');
                    let statusClass = 'needs-review';
                    if (isApproved) statusClass = 'success';
                    else if (!q.needs_review) statusClass = 'available';

                    const optionsCount = q.options ? Object.values(q.options).filter(Boolean).length : 0;
                    const reasonsStr = q.review_reasons ? q.review_reasons.map(r => `<span class="math-symbol-flag">${r}</span>`).join(' ') : '';
                    const answerStr = q.correct_option || q.answer || '--';

                    return `
                        <tr id="row-${q.id || q.question_number_global}">
                            <td><strong>${q.question_number_global || q.question_number || '-'}</strong></td>
                            <td>${q.subject || '-'}</td>
                            <td>${q.question_number_subject || '-'}</td>
                            <td style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${q.question_text ? q.question_text : ''}</td>
                            <td>${optionsCount} / 4</td>
                            <td><strong>${answerStr}</strong></td>
                            <td>${q.has_diagram ? '🖼️ Yes' : 'No'}</td>
                            <td>${q.page_number || q.source_page || '-'}</td>
                            <td>${q.parse_confidence || q.extraction_confidence || '-'}</td>
                            <td><span class="review-status-badge ${statusClass}" id="badge-${q.id || q.question_number_global}">${statusText}</span></td>
                            <td style="max-width: 200px;">${reasonsStr || '--'}</td>
                            <td><button class="btn btn-outline btn-sm" onclick="openDetailsModal('${q.id || q.question_number_global}')">Review</button></td>
                        </tr>
                    `;
                }).join('');
            }

            document.getElementById('triage-loading').style.display = 'none';
            document.getElementById('triage-result-container').style.display = 'block';
        }
        
        async function fetchPapers() {
            try {
                const res = await fetch(`${API_BASE}/api/v1/admin/papers`, { headers: getAuthHeaders() });
                if (res.ok) {
                    const papers = await res.json();
                    document.getElementById('total-papers-count').innerText = papers.length;
                    const tbody = document.getElementById('papers-tbody');
                    if(tbody) {
                        if (papers.length === 0) {
                            tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;">No papers found.</td></tr>';
                        } else {
                            tbody.innerHTML = papers.map(p => `
                                <tr>
                                    <td><strong>${p.title}</strong></td>
                                    <td>${p.year}</td>
                                    <td>${p.set_code || '-'}</td>
                                    <td>${p.paper_type || '-'}</td>
                                    <td>${p.subjects_included || '-'}</td>
                                    <td>${p.expected_question_count || 180}</td>
                                    <td>${p.parsed_question_count}</td>
                                    <td><span style="color: ${p.needs_review_count > 0 ? '#ef4444' : 'inherit'}">${p.needs_review_count}</span></td>
                                    <td><span class="review-status-badge ${p.import_status === 'approved' ? 'success' : ''}">${p.import_status}</span></td>
                                    <td><button class="btn btn-outline btn-sm" disabled>View</button></td>
                                </tr>
                            `).join('');
                        }
                    }
                }
            } catch (err) {
                console.error("Failed to fetch papers", err);
            }
        }
"""

html = re.sub(r'// Parse AG Triage JSON output.*?async function approveQuestion', js_updates + '\n\n        async function approveQuestion', html, flags=re.DOTALL)

# Add fetchPapers call on load dashboard
html = html.replace('loadPhysicsChapters();', "loadPhysicsChapters();\n            } else if (subject === 'PaperLibrary') {\n                fetchPapers();\n            }")
html = html.replace('loadDashboard();', 'loadDashboard();\n            fetchPapers();')

with open("v1_admin.html", "w", encoding="utf-8") as f:
    f.write(html)

print("v1_admin.html updated successfully!")
