# tools/ — The Execution Layer

Deterministic Python scripts that do the actual work: API calls, data
transformations, file operations, database queries. Each tool is consistent,
testable, and fast.

## Conventions

- **One job per script.** A tool does a single, well-defined task and exits with
  a clear success/failure status.
- **Inputs via CLI args or stdin**, outputs to stdout or a file in `.tmp/`.
  Keep them composable so the agent can chain them.
- **Read secrets from `.env`** (use `python-dotenv`). Never hardcode keys.
- **Fail loudly.** Print a readable error and exit non-zero so the agent can
  detect and recover from failures.
- **Document the contract** at the top of each file: what it does, required
  inputs, expected outputs, and which `.env` keys it needs.

## Template

```python
"""scrape_single_site.py — Fetch and clean one web page.

Inputs:  --url <url>            (required)
Output:  writes markdown to .tmp/<slug>.md and prints the path
Env:     FIRECRAWL_API_KEY
"""
import argparse, os, sys
from dotenv import load_dotenv

load_dotenv()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    # ... do the work ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Add new tools only when no existing tool covers the task.
