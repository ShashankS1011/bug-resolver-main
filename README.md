# Bug Resolver Engine

An autonomous, multi-agent bug resolution system built with **LangGraph**, **LangChain**, and local **Ollama** LLMs.

The system automates the software bug resolution lifecycle by ingesting GitHub issues, navigating the codebase to identify root causes, generating code patches and unit tests, executing test suites within a secure sandbox, and automatically creating a Pull Request on GitHub after successful validation.

---

# Key Features

- **Multi-Agent Architecture:** Utilises specialised agents (Reader, Navigator, Developer, Tester, and PR Agent) orchestrated through a LangGraph state machine.
- **Autonomous Debugging Workflow:** Implements an iterative feedback loop in which failing test cases are analysed and the generated patch is refined until all tests pass or a predefined retry limit is reached.
- **Sandboxed Test Execution:** Executes Pytest suites in an isolated environment to validate generated fixes before applying changes to the target repository.
- **GitHub Integration:** Integrates with GitHub via **PyGithub** to retrieve issues, create fix branches, commit validated changes, and automatically open Pull Requests.
- **Local LLM Support:** Supports local deployment using open-source large language models served through Ollama.

---

# System Architecture

```text
                   GitHub Issue
                        │
                        ▼
         Reader Agent
 (Extracts issue details and symptoms)
                        │
                        ▼
        Navigator Agent
 (Identifies target files and root cause)
                        │
                        ▼
        Developer Agent ─────────────┐
 (Generates code patch & unit tests) │
                        │            │
                        ▼            │
          Tester Agent               │
 (Executes Pytest in sandbox)        │
                        │            │
            Tests Fail ──────────────┘
            (Feedback for refinement)

            Tests Pass
                        │
                        ▼
             PR Agent
 (Creates branch, commits changes,
      and opens Pull Request)
                        │
                        ▼
               GitHub Pull Request
```

---

# Project Structure

```text
bug-resolver-main/
├── src/
│   ├── agents/
│   │   ├── investigator_agents.py   # Reader & Navigator agents
│   │   ├── developer_agents.py      # Developer & Tester agents
│   │   └── pr_agent.py              # GitHub Pull Request agent
│   ├── graph.py                     # LangGraph workflow definition
│   └── state.py                     # Shared workflow state
├── test_graph.py                    # End-to-end execution script
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment variable template
└── README.md
```

---

# Setup and Installation

## Prerequisites

- Python 3.10 or later
- Ollama installed and running locally with a supported model (e.g., `llama3` or `qwen2.5-coder`)

## Installation

```bash
git clone https://github.com/ShashankS1011/bug-resolver-main.git
cd bug-resolver-main
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root directory:

```env
GITHUB_TOKEN=your_github_personal_access_token_here
```

Ensure that the GitHub Fine-Grained Personal Access Token has the following permissions:

- **Contents:** Read and Write
- **Pull Requests:** Read and Write
- **Issues:** Read

---

# Usage

By default, the workflow executes against the sample repository:

**Target Repository:** https://github.com/ShashankS1011/bug-resolver

Run the end-to-end workflow using:

```bash
python test_graph.py
```

### Example Execution

```text
Starting LangGraph Bug Resolver against repository
'ShashankS1011/bug-resolver'...

[Reader Agent] Analysing GitHub issue...
[Navigator Agent] Identifying target files...
[Developer Agent] Generating code patch and unit tests...
[Tester Agent] Executing Pytest suite in sandbox...

[Workflow] Tests passed successfully.

[PR Agent] Creating Pull Request...
Pull Request created successfully:
https://github.com/ShashankS1011/bug-resolver/
```
## Test Repository

The Bug Resolver Engine is configured to run against the following sample repository for demonstration and evaluation purposes:

**Repository:** https://github.com/ShashankS1011/bug-resolver

This repository contains intentionally reproducible issues and serves as the target codebase for validating the end-to-end workflow, including issue analysis, automated patch generation, sandboxed test execution, and Pull Request creation.
