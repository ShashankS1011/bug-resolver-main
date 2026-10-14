# Bug Resolver Engine

Bug Resolver Engine is a local, multi-agent workflow that investigates a GitHub issue, proposes a Python fix, tests it in a sandbox, and—when validation succeeds—opens a pull request with the change.

It uses LangGraph for orchestration, Ollama for local language-model inference, PyGithub for GitHub operations, and Pytest for validation.

## How it works

```text
GitHub issue
    |
    v
Reader -> Navigator -> Developer -> Tester
                              ^       |
                              |       v
                         retry      PR Agent -> Pull request
```

1. Reader extracts the issue symptoms and expected behavior.
2. Navigator selects a repository file using the issue and AST information.
3. Developer generates a patch and tests.
4. Tester runs the generated tests in Docker, or uses the local fallback when Docker is unavailable.
5. Failed tests return feedback to Developer until the retry limit is reached.
6. PR Agent creates a fix branch, commits the validated file, and opens a pull request.

## Requirements

- Python 3.10 or newer
- An Ollama installation running locally
- A coding model available in Ollama, such as `qwen2.5-coder:3b`
- Docker Desktop is recommended for isolated test execution
- A GitHub fine-grained token with repository Contents and Pull requests read/write access, plus Issues read access

## Installation

```bash
git clone https://github.com/ShashankS1011/bug-resolver-main.git
cd bug-resolver-main
python -m venv .venv
```

Activate the environment, then install the dependencies:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
```

Install and start Ollama, then download the configured model:

```bash
ollama pull qwen2.5-coder:3b
```

## Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=github_pat_your_token_here
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_BASE_URL=http://localhost:11434
```

The PR agent fails safely when `GITHUB_TOKEN` is missing; it does not report a simulated pull request as a successful result. Never commit `.env` or a real token.

## Run the tests

The deterministic test suite does not require Ollama or a live GitHub repository:

```bash
pytest
```

The CI workflow tests Python 3.10, 3.11, and 3.12, and also runs coverage, Ruff, and mypy checks.

## Running the workflow

The workflow is assembled by `build_bug_resolver_graph()` in `src/graph.py`. Supply a `BugResolverState` containing the repository owner/name, issue number, issue context, repository files, and the configured iteration limits. The public agent nodes can also be imported individually from `src.agents`.

The final PR step requires a real token and a writable repository. It validates the target path and patch before creating a branch. If a GitHub operation fails, the workflow returns `status="FAILED"`, includes the error in `pr_error`, and attempts to remove any partially created fix branch.

## Project layout

```text
src/
  agents/
    investigator_agents.py   # Reader and Navigator
    developer_agents.py      # Developer and Tester
    pr_agent.py              # Validated GitHub branch and PR creation
  graph.py                   # LangGraph workflow
  state.py                   # Shared state schema
tests/
  test_core.py               # Unit and regression tests
requirements.txt             # Python dependencies
requirements-dev.txt         # Pinned test, coverage, lint, and type-check tools
pyproject.toml               # Pytest, coverage, Ruff, and mypy configuration
```

## Safety notes

- Generated code is tested before the PR agent is reached.
- Repository paths must be relative and must not contain traversal components.
- Empty patches and ambiguous target-file selections are rejected.
- Branch creation uses collision-resistant names and retries GitHub branch collisions.
- GitHub failures are surfaced as failed workflow state rather than hidden behind a fake URL.

## Continuous integration

Every push and pull request to `main` runs the GitHub Actions workflow in `.github/workflows/tests.yml`.
The matrix runs the test suite on Python 3.10, 3.11, and 3.12. A quality job also enforces Ruff linting
and mypy type checking. Dependencies are pinned in `requirements.txt` and `requirements-dev.txt` so
local and CI installations use reproducible versions.
