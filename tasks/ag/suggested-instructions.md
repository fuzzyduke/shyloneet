# AG Suggested Instructions

## Aider Task Automation

When using Aider on Windows inside a script, the `--no-git` flag and explicitly specifying `--file <path>` helps prevent Aider from hanging waiting for interactive prompts (like adding files to chat or creating git commits).

Additionally, when running under automated environments that may not support full terminal features (e.g. prompt-toolkit Unicode dependencies), running Aider with redirected input/output or expecting occasional crash on exit (due to Unicode block characters) is a known edge case.

**Best Practice:**
- Provide clear layout models (e.g., "copy the CSS variables from `v1.html`") so Aider can recreate the design perfectly in a single zero-shot attempt.

## Token/Credit Reflection

### Was Aider delegation useful?
No

### AG Context Used
Low

### Aider Context Used
Low (Aborted before completion)

### What caused token waste?
- Aider was unable to initialize properly due to missing Python environment dependencies (Python 3.14 incompatibility with numpy `pkgutil.ImpImporter`) and unconfigured LLM API keys in the IDE sandbox. This required AG to attempt several troubleshooting command executions before ultimately implementing the patch directly.

### How to improve next delegation
- Ensure the execution environment (Python version, dependencies, `.env` file containing API keys/base URL) is stable and fully configured *before* delegating tasks to Aider in a background process.
- Avoid passing tasks to Aider if the environment variables/API keys from earlier steps were lost or not explicitly persisted.

### Should this become a suggested instruction?
Yes
