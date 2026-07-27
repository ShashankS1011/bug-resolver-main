# 🚀 Bug Resolver Engine

An autonomous, multi-agent bug resolution system built with **LangGraph**, **LangChain**, and local **Ollama** LLMs. 

The system automates the entire software bug lifecycle: it ingests GitHub issues, navigates the codebase to locate root causes, drafts code patches and unit tests, executes test suites in a secure sandbox, and automatically creates a live Pull Request on GitHub upon passing tests.

---

## 🌟 Key Features

- **Multi-Agent Architecture:** Powered by specialized agents (Reader, Navigator, Developer, Tester, and PR Agent) orchestrated with a state machine.
- **Autonomous Fix & Test Loop:** Uses a feedback loop where failing tests prompt the Developer Agent to refine the patch until all tests pass or max iterations are reached.
- **Subprocess Sandbox Testing:** Executes Pytest suites inside an isolated execution environment before touching production code.
- **Live GitHub Integration:** Interacts directly with GitHub via `PyGithub` to pull issues, push fix branches, and open automated Pull Requests.
- **Local Model Support:** Operates seamlessly with local open-source LLMs via Ollama.

---

## 🏗️ System Architecture

```text
[ GitHub Issue ]
       │
       ▼
 🔍 Reader Agent (Extracts symptoms & error patterns)
       │
       ▼
 🧭 Navigator Agent (Pinpoints target file & root cause)
       │
       ▼
 💻 Developer Agent ◄───┐ (Drafts patch & unit test)
       │                │
       ▼                │ Retries on test failure
 🧪 Tester Agent ───────┘ (Runs Pytest in sandbox)
       │ (Tests Pass)
       ▼
 🚀 PR Agent (Creates branch, commits fix, & opens PR)
       │
       ▼
[ Live GitHub PR ]
```
# 📁 Project Structure

```text
bug-resolver-main/
├── src/
│   ├── agents/
│   │   ├── investigator_agents.py  # Reader & Navigator agents
│   │   ├── developer_agents.py     # Developer & Tester agents
│   │   └── pr_agent.py             # GitHub PR creation agent
│   ├── graph.py                    # LangGraph workflow definition & routing
│   └── state.py                    # TypedDict state management
├── test_graph.py                   # End-to-end test runner
├── requirements.txt                # Python dependencies
├── .env.example                    # Sample environment variable setup
└── README.md
```

---

# ⚙️ Setup & Installation

## 1. Prerequisites

- Python 3.10+
- Ollama installed and running locally with your preferred model (e.g., `llama3` or `qwen2.5-coder`)

## 2. Install Dependencies

```bash
git clone https://github.com/ShashankS1011/bug-resolver-main.git
cd bug-resolver-main
pip install -r requirements.txt
```

## 3. Environment Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_personal_access_token_here
```

> **Note:** Ensure your GitHub Fine-Grained Personal Access Token has the following permissions:
>
> - **Contents:** Read & Write
> - **Pull Requests:** Read & Write
> - **Issues:** Read

---

# 🚀 Usage

Run the end-to-end pipeline against the target repository:

```bash
python test_graph.py
```

### Sample Output

```text
🚀 Starting LangGraph Bug Resolver against live repo 'ShashankS1011/bug-resolver'...

🔍 [Reader Agent] Analyzing GitHub Issue...
🧭 [Navigator Agent] Pinpointing bug location...
💻 [Developer Agent] Drafting code fix and unit tests...
🧪 [Tester Agent] Executing Pytest suite in sandbox...

🎉 [Graph Router] Tests passed! Proceeding to PR Agent.

🚀 [PR Agent] Opening Pull Request on GitHub...
✅ Pull Request successfully opened:
https://github.com/ShashankS1011/bug-resolver/
```
