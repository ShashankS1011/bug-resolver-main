import json
import re
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.state import BugResolverState
from src.tools.docker_sandbox import DockerSandbox

llm = ChatOllama(
    model="qwen2.5-coder:3b",
    temperature=0.1
)

sandbox = DockerSandbox()

# -------------------------------------------------------------------
# 1. DEVELOPER AGENT NODE
# -------------------------------------------------------------------

def parse_developer_output(text: str) -> Dict[str, str]:
    """Parses developer agent response using string/regex markers."""
    patched_code = ""
    test_code = ""
    explanation = "Fix generated."

    # 1. Try extracting backtick code blocks first if present
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', text, re.DOTALL)
    if len(code_blocks) >= 2:
        return {
            "patched_code": code_blocks[0].strip(),
            "test_code": code_blocks[1].strip(),
            "explanation": explanation
        }

    # 2. Key-marker extraction fallback
    if "PATCHED_CODE:" in text:
        parts = text.split("PATCHED_CODE:", 1)[1]
        if "TEST_CODE:" in parts:
            patch_part, test_part = parts.split("TEST_CODE:", 1)
            patched_code = patch_part.replace("```python", "").replace("```", "").strip()
            
            if "EXPLANATION:" in test_part:
                t_part, exp_part = test_part.split("EXPLANATION:", 1)
                test_code = t_part.replace("```python", "").replace("```", "").strip()
                explanation = exp_part.strip()
            else:
                test_code = test_part.replace("```python", "").replace("```", "").strip()

    return {
        "patched_code": patched_code,
        "test_code": test_code,
        "explanation": explanation
    }


DEVELOPER_PROMPT = ChatPromptTemplate.from_template("""
You are a Senior Python Developer fixing a bug.

BUG DESCRIPTION:
{symptoms}

TARGET FILE: {target_file}

ORIGINAL CODE:
{original_code}

PREVIOUS TEST FEEDBACK:
{feedback}

Fix the bug and write pytest unit tests.
You MUST output your response using EXACTLY this format:

PATCHED_CODE:
def calculate_average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

TEST_CODE:
import pytest
from math_ops.stats import calculate_average

def test_empty():
    assert calculate_average([]) == 0.0

def test_normal():
    assert calculate_average([1, 2, 3]) == 2.0

EXPLANATION:
Added guard clause for empty lists.
""")

def developer_agent_node(state: BugResolverState) -> Dict[str, Any]:
    """Node that drafts a code fix and a corresponding Pytest test suite."""
    print("\n💻 [Developer Agent] Drafting code fix and unit tests...")
    
    target_files = state.get("target_files", [])
    target_file = target_files[0] if target_files else "math_ops/stats.py"
    original_code = state.get("code_context", {}).get(target_file, "# File empty")
    
    test_results = state.get("test_results") or {}
    feedback = test_results.get("output", "None - First attempt")

    prompt = DEVELOPER_PROMPT.format(
        symptoms=state.get("issue_title", ""),
        target_file=target_file,
        original_code=original_code,
        feedback=feedback
    )
    
    response = llm.invoke(prompt)
    
    # CALL OUR PLAIN TEXT PARSER HERE (NOT json.loads!)
    dev_result = parse_developer_output(response.content)
    
    patched_code = dev_result.get("patched_code") or original_code
    test_code = dev_result.get("test_code") or ""
    explanation = dev_result.get("explanation") or "Fix generated."

    chain_log = f"Developer Agent drafted fix for {target_file}. Explanation: {explanation}"
    
    return {
        "patch_code": patched_code,
        "test_code": test_code,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
    }


# -------------------------------------------------------------------
# 2. TESTER AGENT NODE
# -------------------------------------------------------------------

def tester_agent_node(state: BugResolverState) -> Dict[str, Any]:
    print("🧪 [Tester Agent] Executing Pytest suite in sandbox...")
    
    target_files = state.get("target_files", [])
    target_file = target_files[0] if target_files else "math_ops/stats.py"
    
    code_files = {
        target_file: state.get("patch_code", "")
    }
    test_code = state.get("test_code", "")

    # Reject empty or fallback tests
    if not test_code or "test_fallback" in test_code or len(test_code.strip()) < 10:
        result = {
            "passed": False,
            "output": "Tester Agent Error: Developer failed to produce a valid unit test suite."
        }
    else:
        result = sandbox.run_tests_in_sandbox(code_files, test_code)
    
    status = "PASSED" if result["passed"] else "IN_PROGRESS"
    chain_log = f"Tester Agent run completed. Passed: {result['passed']}"

    return {
        "test_results": result,
        "status": status,
        "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
    }