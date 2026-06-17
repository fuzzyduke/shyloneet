import re

with open('admin_review.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add paper dropdown
dropdown_html = """
        <div style="margin-bottom: 1rem; display: flex; align-items: center; gap: 1rem;">
            <label style="font-weight: bold;">Select Paper:</label>
            <select id="global-paper-select" onchange="onPaperChange()" style="padding: 0.5rem; border-radius: 4px; border: 1px solid var(--border-color); width: 300px;">
                <option value="">Loading papers...</option>
            </select>
        </div>
"""
if 'global-paper-select' not in html:
    html = html.replace('<h1>Admin Review Dashboard</h1>', '<h1>Admin Review Dashboard</h1>' + dropdown_html)

# 2. Add Simple View Tab
simple_tab = '<button class="tab-btn active" id="tab-simple_view" onclick="switchTab(\'simple_view\')">Simple View</button>'
if 'tab-simple_view' not in html:
    html = html.replace('<button class="tab-btn active" id="tab-mandatory_review"', simple_tab + '\n            <button class="tab-btn" id="tab-mandatory_review"')

# 3. Add Simple View Content Container
simple_content = '<div id="content-simple_view" class="tab-content active">Loading simple view...</div>'
if 'content-simple_view' not in html:
    html = html.replace('<div id="tab-contents">', '<div id="tab-contents">\n            ' + simple_content)

# 4. JS Globals
if 'let currentPaperId = null;' not in html:
    html = html.replace('let chapters = [];', 'let chapters = [];\n        let currentPaperId = null;')

# 5. JS initialization
init_addition = """
            await loadPapersForDropdown();
            // loadSummary and loadQueues will be called by loadPapersForDropdown or onPaperChange
"""
# Need to remove the direct calls to loadSummary and loadQueues in init() to avoid racing
html = re.sub(r'await loadSummary\(\);\s+await loadQueues\(\);', init_addition, html)

# 6. Dropdown load functions
dropdown_funcs = """
        async function loadPapersForDropdown() {
            const res = await fetch(`${API_BASE}/api/papers`, { headers: getHeaders() });
            const papers = await res.json();
            const select = document.getElementById('global-paper-select');
            select.innerHTML = '';
            if (papers.length === 0) {
                select.innerHTML = '<option value="">No papers available</option>';
                return;
            }
            papers.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = `${p.exam_type} ${p.year} (Code: ${p.paper_code})`;
                select.appendChild(opt);
            });
            currentPaperId = papers[0].id;
            await refreshUI();
        }

        async function onPaperChange() {
            currentPaperId = document.getElementById('global-paper-select').value;
            await refreshUI();
        }
"""
if 'loadPapersForDropdown' not in html:
    html = html.replace('async function init() {', dropdown_funcs + '\n        async function init() {')

# 7. Update fetch URLs to include paper_id
html = html.replace('fetch(`${API_BASE}/api/admin/review-summary`', 'fetch(`${API_BASE}/api/admin/review-summary?paper_id=${currentPaperId || \'\'}`')
html = html.replace('fetch(`${API_BASE}/api/admin/review-queue`', 'fetch(`${API_BASE}/api/admin/review-queue?paper_id=${currentPaperId || \'\'}`')
html = html.replace('fetch(`${API_BASE}/api/admin/subadmin-corrections`', 'fetch(`${API_BASE}/api/admin/subadmin-corrections?paper_id=${currentPaperId || \'\'}`')

# 8. Build Simple View inside loadQueues
build_simple_view_code = """
            // Build Simple View
            buildSimpleView(queues);
"""
# inject right before `const sections = [`
if 'buildSimpleView' not in html:
    html = html.replace('const sections = [', build_simple_view_code + '\n            const sections = [')

# 9. Simple View Builder Function
builder_funcs = """
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
"""
if 'function buildSimpleView' not in html:
    html = html.replace('function renderItem(item, type) {', builder_funcs + '\n        function renderItem(item, type) {')

# 10. Add ID to q-card for jumping
html = html.replace('<div class="review-card q-card"', '<div class="review-card q-card" id="qcard-${item.question ? item.question.id : item.id}"')

with open('admin_review.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("admin_review.html successfully patched!")
