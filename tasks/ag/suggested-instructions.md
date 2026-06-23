# AG Suggested Instructions

## Aider Task Automation

When using Aider on Windows inside a script, the `--no-git` flag and explicitly specifying `--file <path>` helps prevent Aider from hanging waiting for interactive prompts (like adding files to chat or creating git commits).

Additionally, when running under automated environments that may not support full terminal features (e.g. prompt-toolkit Unicode dependencies), running Aider with redirected input/output or expecting occasional crash on exit (due to Unicode block characters) is a known edge case.

**Best Practice:**
- Explicitly add files to Aider using the `--file` flag via command line to avoid interactive confirmation prompts inside background/automated sessions.
- Provide clear layout models (e.g., "copy the CSS variables from `v1.html`") so Aider can recreate the design perfectly in a single zero-shot attempt.
