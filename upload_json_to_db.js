const fs = require('fs');

async function importQuestions() {
    console.log("Reading paper_triage_mock.json...");
    const data = JSON.parse(fs.readFileSync('paper_triage_mock.json', 'utf8'));
    
    // Using the live HTTPS domain
    const API_BASE = 'https://shyloneetv1.valhallala.com';
    let successCount = 0;
    
    const metadata = data.paper || data.metadata;
    const questions = data.questions;
    
    console.log(`Found ${questions.length} questions. Starting import to ${API_BASE}...`);
    
    for (let i = 0; i < questions.length; i++) {
        const q = questions[i];
        const payload = {
            metadata: metadata,
            question: q
        };
        
        try {
            const res = await fetch(`${API_BASE}/api/v1/admin/triage/import_question`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer bypass-dev-token'
                },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                successCount++;
                if (successCount % 10 === 0) {
                    console.log(`Successfully imported ${successCount} questions...`);
                }
            } else {
                console.error(`Failed to import question ${q.question_number_global}: ${res.status} ${res.statusText}`);
                const text = await res.text();
                console.error(`Response body: ${text}`);
            }
        } catch (e) {
            console.error(`Error importing question ${q.question_number_global}: ${e.message}`);
        }
    }
    
    console.log(`\nImport complete! Successfully imported ${successCount}/${questions.length} questions.`);
}

importQuestions();
