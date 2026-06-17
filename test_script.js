
        const API_BASE = 'http://localhost:8000';
        let chapters = [];
        let currentPaperId = null;
        let chapterOptionsHTML = '';

        async function init() {
            try {
                // Fetch boundary restricted chapters
                const chapRes = await fetch(`${API_BASE}/api/chapters?exam_program_id=NEET&subject=Physics&source=NCERT&class_level=12`);
                chapters = await chapRes.json();
                chapterOptionsHTML = chapters.map(c => `<option value="${c.id}">${c.chapter_name}</option>`).join('');
                
                
            await loadPapersForDropdown();
            // loadSummary and loadQueues will be called by loadPapersForDropdown or onPaperChange

                await loadPapers();
            } catch (e) {
                console.error(e);
                document.getElementById('summary-dashboard').innerHTML = `<p class="error">Error connecting to backend API.</p>`;
            }
        }

        async function loadSummary() {
            const res = await fetch(`${API_BASE}/api/admin/review-summary?paper_id=${currentPaperId || ''}`);
            const data = await res.json();
            
            document.getElementById('summary-dashboard').innerHTML = `
                <div class="summary-card"><h3>${data.total_unique}</h3><p>Total Unique</p></div>
                <div class="summary-card"><h3>${data.mandatory_review}</h3><p>Mandatory Review</p></div>
                <div class="summary-card"><h3>${data.unmapped}</h3><p>Unmapped</p></div>
                <div class="summary-card"><h3>${data.review_recommended}</h3><p>Review Recommended</p></div>
                <div class="summary-card"><h3>${data.failed_extractions}</h3><p>Failed Extractions</p></div>
                <div class="summary-card" style="border-color: var(--primary-color);"><h3>${data.auto_approved}</h3><p style="color: var(--primary-color);">Auto-Approved (Student UI)</p></div>
            `;
        }

        async function loadQueues() {
            const res = await fetch(`${API_BASE}/api/admin/review-queue?paper_id=${currentPaperId || ''}`, { headers: getHeaders() });
            const queues = await res.json();
            
            const shilohRes = await fetch(`${API_BASE}/api/admin/subadmin-corrections?paper_id=${currentPaperId || ''}`, { headers: getHeaders() });
            const shilohData = await shilohRes.json();
            
            const tabContents = document.getElementById('tab-contents');
            tabContents.innerHTML = '';
            
            
            // Build Simple View
            buildSimpleView(queues);

            const sections = [
                { id: 'mandatory_review', label: 'Mandatory Review', data: queues.mandatory_review, type: 'mapped' },
                { id: 'unmapped', label: 'Unmapped', data: queues.unmapped, type: 'unmapped' },
                { id: 'review_recommended', label: 'Review Recommended', data: queues.review_recommended, type: 'mapped' },
                { id: 'failed_extractions', label: 'Failed Extractions', data: queues.failed_extractions, type: 'failed' },
                { id: 'shiloh_corrections', label: 'Shiloh Corrections', data: shilohData, type: 'shiloh' },
                { id: 'auto_approved', label: 'Auto-Approved', data: queues.auto_approved, type: 'mapped' }
            ];
            
            sections.forEach((sec, idx) => {
                const isActive = sec.id === 'mandatory_review' ? 'active' : '';
                let contentHTML = '';
                
                if (sec.data.length === 0) {
                    contentHTML = `<p>No questions in this queue.</p>`;
                } else {
                    contentHTML = sec.data.map(item => renderItem(item, sec.type)).join('');
                }
                
                // Update tab count
                const tabBtn = document.getElementById(`tab-${sec.id}`);
                if (tabBtn) {
                    tabBtn.innerHTML = `${sec.label} (${sec.data.length})`;
                }
                
                tabContents.innerHTML += `<div id="content-${sec.id}" class="tab-content ${isActive}">${contentHTML}</div>`;
            });
        }
        
        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(`content-${tabId}`).classList.add('active');
        }

        
        function buildSimpleView(queues) {
            let allQuestions = [];
            ['auto_approved', 'mandatory_review', 'review_recommended'].forEach(qName => {
                if(queues[qName]) allQuestions.push(...queues[qName]);
            });
            if(queues.unmapped) allQuestions.push(...queues.unmapped);
            
            allQuestions.sort((a,b) => a.question.question_number - b.question.question_number);
            
            let html = `<div class="review-card" style="padding:0; overflow:hidden;"><table style="width:100%; border-collapse:collapse; text-align:left;">
                <thead>
                    <tr style="background:var(--surface-hover); border-bottom:1px solid var(--border-color);">
                        <th style="padding:1rem;">Q.No</th>
                        <th style="padding:1rem;">Snippet</th>
                        <th style="padding:1rem;">Ans</th>
                        <th style="padding:1rem;">Chapter</th>
                        <th style="padding:1rem;">Status</th>
                        <th style="padding:1rem;">Action</th>
                    </tr>
                </thead>
                <tbody>`;
            
            if(allQuestions.length === 0) {
                html += `<tr><td colspan="6" style="padding:1rem; text-align:center;">No questions found for this paper.</td></tr>`;
            }

            allQuestions.forEach(item => {
                const q = item.question;
                const m = item.mapping;
                const snippet = q.question_text ? q.question_text.substring(0, 50).replace(/</g, '&lt;') + '...' : 'No text';
                const ans = q.answer || '-';
                const chap = m ? m.chapter_name : 'Unmapped';
                let status = m ? (m.approved_by_admin ? 'Approved' : 'Needs Review') : 'Unmapped';
                let color = m ? (m.approved_by_admin ? 'success' : 'warning') : 'error';
                
                html += `<tr style="border-bottom:1px solid var(--border-color);">
                    <td style="padding:1rem;">${q.question_number}</td>
                    <td style="padding:1rem; font-size:0.9rem; color:var(--text-muted);">${snippet}</td>
                    <td style="padding:1rem; font-weight:bold;">${ans}</td>
                    <td style="padding:1rem;">${chap}</td>
                    <td style="padding:1rem;"><span class="tag ${color}">${status}</span></td>
                    <td style="padding:1rem;"><button class="btn btn-outline btn-sm" onclick="jumpToAdvanced('${q.id}')">Edit</button></td>
                </tr>`;
            });
            html += `</tbody></table></div>`;
            
            const container = document.getElementById('content-simple_view');
            if(container) container.innerHTML = html;
        }

        function jumpToAdvanced(qId) {
            const card = document.getElementById(`qcard-${qId}`);
            if(card) {
                const tabContent = card.closest('.tab-content');
                if(tabContent) {
                    const tabId = tabContent.id.replace('content-', '');
                    switchTab(tabId);
                    card.scrollIntoView({behavior: 'smooth', block: 'center'});
                    card.style.border = '2px solid var(--primary-color)';
                    setTimeout(() => card.style.border = '1px solid var(--border-color)', 2000);
                }
            } else {
                alert('Question not found in advanced queues.');
            }
        }

        function renderItem(item, type) {
            if (type === 'failed') {
                return `
                <div class="review-card">
                    <h3>Failed Extraction</h3>
                    <p><strong>Page:</strong> ${item.page_number} | <strong>Column:</strong> ${item.column_name}</p>
                    <p><strong>Parse Error:</strong> ${item.parse_error}</p>
                    <pre style="background:var(--background); padding:1rem; overflow-x:auto;">${item.raw_response}</pre>
                </div>`;
            } else if (type === 'shiloh') {
                return `
                <div class="review-card">
                    <h3>Q${item.question_number} - Shiloh Correction Pending</h3>
                    <p><strong>Suggested Option:</strong> ${item.proposed_option}</p>
                    <p><strong>Reasoning:</strong> ${item.reasoning || 'N/A'}</p>
                    <div style="display:flex; gap:1rem; margin-top:1rem;">
                        <button class="btn btn-primary" onclick="adminReviewShiloh('${item.evaluation_id}', 'accept')">Accept</button>
                        <button class="btn" style="background:#dc2626; color:white;" onclick="adminReviewShiloh('${item.evaluation_id}', 'revert')">Revert/Reject</button>
                    </div>
                
                <div style="margin-top: 1rem;">
                    <button class="btn" onclick="toggleProvenance('${item.question_id}')">Toggle Provenance & Eval History</button>
                    <div id="prov-${item.question_id}" style="display:none; margin-top:1rem; padding:1rem; background:var(--background); border-radius:8px;">Loading...</div>
                </div>
            </div>`;
            }
            
            const q = item.question;
            const m = item.mapping;
            
            let assetsHTML = q.assets.map(a => `<img src="${a.url}" alt="${a.caption}" style="max-width:100%; margin-top:1rem; border-radius:8px;">`).join('');
            
            let mappingControls = '';
            if (type === 'mapped') {
                const confPercent = m.confidence ? (m.confidence * 100).toFixed(1) + '%' : 'N/A';
                mappingControls = `
                    <div style="margin-top: 1.5rem; background: var(--background); padding: 1rem; border-radius: 8px;">
                        <div style="display:flex; justify-content:space-between;">
                            <h4 style="margin-top:0;">Current Classification</h4>
                            <span class="tag ${m.confidence < 0.7 ? 'warning' : 'success'}">Confidence: ${confPercent}</span>
                        </div>
                        <p><strong>Primary Chapter:</strong> ${m.chapter_name}</p>
                        ${m.secondary_chapters && m.secondary_chapters.length > 0 ? `<p><strong>Secondary:</strong> ${m.secondary_chapters.map(sc => sc.chapter_name).join(', ')}</p>` : ''}
                        <p><strong>Method:</strong> ${m.mapping_method} | <strong>Reason:</strong> <em>${m.reason}</em></p>
                        
                        <div style="margin-top: 1rem;">
                            <label><strong>Change Primary Chapter:</strong></label>
                            <select id="primary-${q.id}" style="width: 100%; padding: 0.5rem; margin-top: 0.5rem;">
                                <option value="${m.chapter_id}" selected>${m.chapter_name}</option>
                                ${chapterOptionsHTML}
                            </select>
                        </div>
                        <div style="margin-top: 1rem;">
                            <label><strong>Secondary Chapters (Hold Ctrl/Cmd):</strong></label>
                            <select id="secondary-${q.id}" multiple style="width: 100%; padding: 0.5rem; margin-top: 0.5rem;">
                                ${chapterOptionsHTML}
                            </select>
                        </div>
                        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                            <button onclick="updateMapping('${q.id}')" class="btn btn-primary" style="flex: 2;" accesskey="s">Save Mapping & Next (Alt+S)</button>
                            ${m.approved_by_admin ? '' : `<button onclick="approveMapping('${q.id}')" class="btn btn-primary" style="flex: 1;" accesskey="a">✅ Approve & Next (Alt+A)</button>`}
                        </div>
                    </div>
                `;
            } else if (type === 'unmapped') {
                mappingControls = `
                    <div style="margin-top: 1.5rem; background: var(--background); padding: 1rem; border-radius: 8px;">
                        <h4 style="margin-top:0; color: #991b1b;">No Chapter Assigned</h4>
                        <div style="margin-top: 1rem;">
                            <label><strong>Assign Primary Chapter:</strong></label>
                            <select id="primary-${q.id}" style="width: 100%; padding: 0.5rem; margin-top: 0.5rem;">
                                <option value="">-- Select Chapter --</option>
                                ${chapterOptionsHTML}
                            </select>
                        </div>
                        <div style="margin-top: 1rem;">
                            <label><strong>Secondary Chapters (Hold Ctrl/Cmd):</strong></label>
                            <select id="secondary-${q.id}" multiple style="width: 100%; padding: 0.5rem; margin-top: 0.5rem;">
                                ${chapterOptionsHTML}
                            </select>
                        </div>
                        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                            <button onclick="updateMapping('${q.id}')" class="btn btn-primary" style="flex: 1;" accesskey="s">Save Mapping & Next (Alt+S)</button>
                        </div>
                    </div>
                `;
            }

            return `
                <div class="review-card q-card" id="qcard-${item.question ? item.question.id : item.id}" id="card-${q.id}" data-qnum="${q.question_number}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <h3 style="margin-top:0">Q${q.question_number} <span style="font-size: 0.8rem; font-family: monospace; color:var(--text-muted);">(${q.id.split('-')[0]})</span></h3>
                    </div>
                    
                    <p style="font-size: 1.1rem; margin: 1rem 0;">${q.question_text.replace(/\\n/g, '<br>')}</p>
                    ${assetsHTML}
                    
                    <div class="options-grid">
                        <div class="option-box"><strong>A.</strong> ${q.options.A || 'N/A'}</div>
                        <div class="option-box"><strong>B.</strong> ${q.options.B || 'N/A'}</div>
                        <div class="option-box"><strong>C.</strong> ${q.options.C || 'N/A'}</div>
                        <div class="option-box"><strong>D.</strong> ${q.options.D || 'N/A'}</div>
                    </div>
                    
                    <div style="background:var(--surface-hover); padding:1rem; margin-top:1rem; border-radius:8px;">
                        <h4 style="margin-top:0;">Solution & Scoring</h4>
                        <div style="display:flex; gap: 1rem; margin-bottom: 0.5rem;">
                            <div style="flex:1;">
                                <label><strong>Correct Option:</strong></label>
                                <select id="ans-opt-${q.id}" style="width:100%; padding:0.5rem;">
                                    <option value="" ${!q.answer ? 'selected' : ''}>-- None --</option>
                                    <option value="A" ${q.answer == 'A' || q.answer == '1' ? 'selected' : ''}>Option 1 (A)</option>
                                    <option value="B" ${q.answer == 'B' || q.answer == '2' ? 'selected' : ''}>Option 2 (B)</option>
                                    <option value="C" ${q.answer == 'C' || q.answer == '3' ? 'selected' : ''}>Option 3 (C)</option>
                                    <option value="D" ${q.answer == 'D' || q.answer == '4' ? 'selected' : ''}>Option 4 (D)</option>
                                    <option value="bonus" ${q.answer == 'bonus' ? 'selected' : ''}>Bonus/Grace</option>
                                </select>
                            </div>
                            <div style="flex:1;">
                                <label><strong>Scoring Eligible:</strong></label>
                                <select id="ans-elig-${q.id}" style="width:100%; padding:0.5rem;">
                                    <option value="true" ${q.scoring_eligible !== false ? 'selected' : ''}>Yes</option>
                                    <option value="false" ${q.scoring_eligible === false ? 'selected' : ''}>No</option>
                                </select>
                            </div>
                        </div>
                        <label><strong>Solution Text:</strong></label>
                        <textarea id="ans-sol-${q.id}" rows="3" style="width:100%; padding:0.5rem;">${q.solution || ''}</textarea>
                        <button onclick="updateAnswer('${q.id}')" class="btn btn-outline" style="margin-top:0.5rem;">💾 Save Solution Data</button>
                    </div>
                    
                    ${mappingControls}
                    
                    <div class="meta-info">
                        <span><strong>Source:</strong> ${q.source_pdf} | Page ${q.page_number}</span>
                        <span><strong>Extracted via:</strong> ${q.extraction_model} (${q.extraction_method})</span>
                        ${q.incompatibility_flags ? `<span class="tag error">Flags: ${q.incompatibility_flags}</span>` : ''}
                    </div>
                    
                    <div style="margin-top: 1rem; text-align: right;">
                        <button onclick="markBadExtraction('${q.id}')" class="btn btn-outline" style="border-color: #fca5a5; color: #dc2626; padding: 0.5rem 1rem; font-size:0.85rem;">🗑️ Mark Bad Extraction</button>
                    </div>
                </div>
            `;
        }

        async function approveMapping(questionId) {
            await fetch(`${API_BASE}/api/admin/questions/${questionId}/approve-mapping`, {
                method: 'POST'
            });
            await refreshUI();
        }

        async function updateMapping(questionId) {
            const primarySelect = document.getElementById(`primary-${questionId}`);
            const secondarySelect = document.getElementById(`secondary-${questionId}`);
            
            const primaryId = primarySelect.value;
            if (!primaryId) {
                alert("Please select a primary chapter.");
                return;
            }
            
            const secondaryIds = Array.from(secondarySelect.selectedOptions).map(opt => opt.value);
            
            await fetch(`${API_BASE}/api/admin/questions/${questionId}/update-mapping`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    primary_chapter_id: primaryId,
                    secondary_chapter_ids: secondaryIds
                })
            });
            await refreshUI();
        }

        async function updateAnswer(questionId) {
            const opt = document.getElementById(`ans-opt-${questionId}`).value;
            const elig = document.getElementById(`ans-elig-${questionId}`).value === 'true';
            const sol = document.getElementById(`ans-sol-${questionId}`).value;
            
            await fetch(`${API_BASE}/api/admin/questions/${questionId}/update-answer`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    correct_option: opt || null,
                    solution_text: sol || null,
                    scoring_eligible: elig,
                    answer_status: opt ? 'manual_admin' : 'unavailable',
                    solution_source: opt ? 'manual_admin' : 'none',
                    solution_needs_review: false
                })
            });
            alert('Solution updated!');
            await refreshUI();
        }

        async function markBadExtraction(questionId) {
            if(!confirm("Are you sure you want to mark this extraction as bad? It will be removed from student UI.")) return;
            
            await fetch(`${API_BASE}/api/admin/questions/${questionId}/mark-bad-extraction`, {
                method: 'POST'
            });
            await refreshUI();
        }

        async function refreshUI() {
            await loadSummary();
            await loadQueues();
            if (typeof filterQuestions === 'function') {
                filterQuestions();
            }
        }

        function filterQuestions() {
            const query = document.getElementById('q-search').value.trim();
            const cards = document.querySelectorAll('.q-card');
            cards.forEach(card => {
                if (!query) {
                    card.style.display = 'block';
                    return;
                }
                const qNum = card.getAttribute('data-qnum');
                if (qNum === query) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function getHeaders() {
            const token = localStorage.getItem('auth_token');
            return token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
        }

        async function loadPapers() {
            const res = await fetch(`${API_BASE}/api/papers`, { headers: getHeaders() });
            const papers = await res.json();
            let html = `<h3>Paper Solutions & AI Processing</h3>`;
            
            papers.forEach(p => {
                html += `
                <div style="background:var(--background); padding:1rem; border-radius:8px; margin-bottom:1rem;">
                    <h4>${p.exam_type} ${p.year} (Code: ${p.paper_code})</h4>
                    <div style="display:flex; gap:1rem; align-items:center;">
                        <select id="ai-model-${p.id}" style="padding:0.5rem; border-radius:4px; border:1px solid var(--border-color);">
                            <option value="qwen-3-7-plus">Qwen-3.7-Plus</option>
                            <option value="gpt-5.5">GPT-5.5</option>
                            <option value="grok-4-20-multi-agent">Grok 4.20 Multi-Agent</option>
                        </select>
                        <button class="btn btn-primary" onclick="triggerAIJob('${p.id}', 'answer_and_chapter_mapping')">Run AI Evaluation</button>
                    </div>
                    <div id="ai-jobs-${p.id}" style="margin-top:1rem; font-size:0.85rem; color:var(--text-muted);"></div>
                </div>`;
            });
            const c = document.getElementById('papers-list-container');
            if (c) c.innerHTML = html;
            
            papers.forEach(p => loadAIJobs(p.id));
        }

        async function loadAIJobs(paperId) {
            const res = await fetch(`${API_BASE}/api/admin/papers/${paperId}/ai-processing`, { headers: getHeaders() });
            if(res.ok) {
                const jobs = await res.json();
                const container = document.getElementById(`ai-jobs-${paperId}`);
                if (!container) return;
                
                if(jobs.length > 0) {
                    container.innerHTML = jobs.map(j => `Job ${j.id.split('-')[0]}: ${j.job_type} via ${j.requested_model} - <strong style="color:var(--primary-color)">${j.status}</strong>`).join('<br>');
                } else {
                    container.innerHTML = 'No processing jobs run yet.';
                }
            }
        }

        async function triggerAIJob(paperId, jobType) {
            const model = document.getElementById(`ai-model-${paperId}`).value;
            await fetch(`${API_BASE}/api/admin/papers/${paperId}/ai-processing-jobs`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({ job_type: jobType, requested_model: model })
            });
            alert('AI Processing Job Queued!');
            loadAIJobs(paperId);
        }

        async function toggleProvenance(qId) {
            const div = document.getElementById(`prov-${qId}`);
            if(div.style.display === 'none') {
                div.style.display = 'block';
                div.innerHTML = 'Loading...';
                
                const ansRes = await fetch(`${API_BASE}/api/questions/${qId}/answer-evaluations`, { headers: getHeaders() });
                const ansData = await ansRes.json();
                
                const chapRes = await fetch(`${API_BASE}/api/questions/${qId}/chapter-mapping-evaluations`, { headers: getHeaders() });
                const chapData = await chapRes.json();
                
                let html = `<h5>Answer Evaluations</h5><table style="width:100%; text-align:left; border-collapse:collapse; margin-bottom:1rem; font-size:0.9rem;">
                    <tr style="border-bottom:1px solid var(--border-color);">
                        <th style="padding:0.5rem 0;">Source</th><th>Option</th><th>Conf</th><th>Status</th>
                    </tr>`;
                ansData.forEach(e => {
                    html += `<tr style="border-bottom:1px solid var(--border-color);">
                        <td style="padding:0.5rem 0;">${e.evaluator_type} (${e.evaluator_name})</td>
                        <td>${e.correct_option || '-'}</td>
                        <td>${e.confidence ? (e.confidence*100).toFixed(0)+'%' : '-'}</td>
                        <td><span class="tag ${e.is_active ? 'success' : ''}">${e.status}</span></td>
                    </tr>`;
                });
                if (ansData.length === 0) html += `<tr><td colspan="4" style="padding:0.5rem 0; color:var(--text-muted);">No answer evaluations found.</td></tr>`;
                html += `</table>`;
                
                html += `<h5>Chapter Mapping Evaluations</h5><table style="width:100%; text-align:left; border-collapse:collapse; font-size:0.9rem;">
                    <tr style="border-bottom:1px solid var(--border-color);">
                        <th style="padding:0.5rem 0;">Source</th><th>Primary Chapter</th><th>Conf</th><th>Status</th>
                    </tr>`;
                chapData.forEach(e => {
                    html += `<tr style="border-bottom:1px solid var(--border-color);">
                        <td style="padding:0.5rem 0;">${e.evaluator_type} (${e.evaluator_name})</td>
                        <td>${e.primary_chapter_id || '-'}</td>
                        <td>${e.confidence ? (e.confidence*100).toFixed(0)+'%' : '-'}</td>
                        <td><span class="tag ${e.is_active ? 'success' : ''}">${e.status}</span></td>
                    </tr>`;
                });
                if (chapData.length === 0) html += `<tr><td colspan="4" style="padding:0.5rem 0; color:var(--text-muted);">No chapter mapping evaluations found.</td></tr>`;
                html += `</table>`;
                
                div.innerHTML = html;
            } else {
                div.style.display = 'none';
            }
        }

        async function adminReviewShiloh(evalId, action) {
            await fetch(`${API_BASE}/api/admin/answer-evaluations/${evalId}/${action}`, {
                method: 'POST',
                headers: getHeaders()
            });
            refreshUI();
        }

        window.onload = init;
    