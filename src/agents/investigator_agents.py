import json
from typing import Dict, Any, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.state import BugResolverState
from src.tools.ast_tool import parse_code_structure

# Initialize local LLM pointing to your Ollama installation
llm = ChatOllama(
    model="qwen2.5-coder:3b",
    temperature=0.1
)

# -------------------------------------------------------------------
# 1. READER AGENT NODE
# -------------------------------------------------------------------

READER_PROMPT = ChatPromptTemplate.from_template("""
You are an expert Software Bug Investigator.
Analyze the following GitHub issue and extract the core technical problem details.

ISSUE TITLE:
{issue_title}

ISSUE BODY:
{issue_body}

Respond ONLY in valid JSON with this structure:
{{
  "symptoms": "Brief summary of what went wrong",
  "expected_behavior": "What the user expected to happen",
  "actual_behavior": "What actually happened or error messages",
  "keywords": ["list", "of", "relevant", "functions", "or", "terms"]
}}
""")

def reader_agent_node(state: BugResolverState) -> Dict[str, Any]:
    """Node that ingests issue details and extracts structured bug symptoms."""
    print("\n🔍 [Reader Agent] Analyzing GitHub Issue...")
    
    prompt = READER_PROMPT.format(
        issue_title=state.get("issue_title", ""),
        issue_body=state.get("issue_body", "")
    )
    
    response = llm.invoke(prompt)
    
    try:
        cleaned_json = response.content.strip().strip("```json").strip("```").strip()
        analysis = json.loads(cleaned_json)
    except Exception:
        analysis = {
            "symptoms": state.get("issue_title", ""),
            "expected_behavior": "Unknown",
            "actual_behavior": state.get("issue_body", ""),
            "keywords": []
        }

    chain_log = f"Reader Agent extracted symptoms: {analysis.get('symptoms')}"
    
    return {
        "chain_of_thought": state.get("chain_of_thought", []) + [chain_log],
        "status": "IN_PROGRESS"
    }


# -------------------------------------------------------------------
# 2. NAVIGATOR AGENT NODE
# -------------------------------------------------------------------

NAVIGATOR_PROMPT = ChatPromptTemplate.from_template("""
You are a Codebase Navigation Specialist.
Given a list of file paths in a repository and an issue description, identify which file(s) are most likely responsible for the bug.

ISSUE SUMMARY:
{symptoms}

REPOSITORY FILES:
{repo_files}

AST MAP / KEY FUNCTIONS:
{ast_summary}

Respond ONLY in valid JSON with this structure:
{{
  "target_files": ["path/to/file1.py"],
  "reasoning": "Brief explanation of why these files were selected"
}}
""")

def navigator_agent_node(state: BugResolverState) -> Dict[str, Any]:
    """Node that uses AST summaries and file paths to select target files to edit."""
    print("🧭 [Navigator Agent] Pinpointing bug location...")
    
    repo_files = state.get("repo_files", [])
    code_context = state.get("code_context", {})
    
    # Generate AST summary for any files already loaded in context
    ast_summaries = {}
    for path, content in code_context.items():
        ast_summaries[path] = parse_code_structure(content)

    prompt = NAVIGATOR_PROMPT.format(
        symptoms=state.get("issue_title", ""),
        repo_files=json.dumps(repo_files),
        ast_summary=json.dumps(ast_summaries)
    )
    
    response = llm.invoke(prompt)
    
    try:
        cleaned_json = response.content.strip().strip("```json").strip("```").strip()
        nav_result = json.loads(cleaned_json)
        target_files = nav_result.get("target_files", [])
        reasoning = nav_result.get("reasoning", "")
    except Exception:
        # Fallback if JSON parsing fails
        target_files = repo_files[:1] if repo_files else []
        reasoning = "Fallback default selection."

    chain_log = f"Navigator Agent targeted {target_files}. Reason: {reasoning}"
    
    return {
        "target_files": target_files,
        "ast_summary": ast_summaries,
        "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
    }