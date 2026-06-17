# Admin Review Workflows

The Admin UI (`/admin`) serves as the central command for validating extracted questions, reviewing classification mappings, and arbitrating human/AI answer corrections.

## Authentication & Access
- The route `/admin` strictly enforces JWT-based Auth, requiring the `admin` role.
- Unauthenticated users or `sub_admin` accounts (like Shiloh) are rejected.

## Review Queues
The UI organizes work into actionable tabs:
1. **Mandatory Review:** Questions flagged by low-confidence embeddings or classification drift.
2. **Unmapped:** Questions with zero valid chapter mappings.
3. **Review Recommended:** Mild confidence flags or secondary considerations.
4. **Failed Extractions:** Questions where the Vision Agent failed to parse structured JSON.
5. **Shiloh Corrections:** Pending overrides submitted by `sub_admin` human reviewers.
6. **Auto-Approved:** Cleanly mapped questions meeting threshold criteria.

## Answer Provenance & AI Jobs
- **Shiloh Corrections Arbitration:** Admins can `Accept` or `Revert/Reject` pending Shiloh corrections with one click.
- **AI Processing Queue:** Admins can trigger Paper-level AI jobs (e.g., Qwen, Grok, GPT) to batch-evaluate mapping and answers. Results append to the Provenance tables instead of destructively overwriting data.
- **Provenance Drill-Down:** Admins can toggle the full Evaluation History per question, viewing the exact chronology of Paper -> AI -> Shiloh -> Admin mapping attempts.
