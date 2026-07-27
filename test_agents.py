from src.agents.investigator_agents import reader_agent_node, navigator_agent_node
from src.state import BugResolverState

# Mock initial state representing an incoming GitHub issue
mock_state: BugResolverState = {
    "repo_owner": "test_owner",
    "repo_name": "test_repo",
    "issue_number": 1,
    "issue_title": "Division by zero crash in calculate_average",
    "issue_body": "When providing an empty list to calculate_average(), the system throws ZeroDivisionError instead of returning 0.0.",
    "repo_files": ["math_ops/stats.py", "math_ops/trig.py", "main.py"],
    "code_context": {
        "math_ops/stats.py": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n"
    },
    "target_files": [],
    "ast_summary": {},
    "patch_code": None,
    "test_code": None,
    "test_results": None,
    "iteration_count": 0,
    "max_iterations": 3,
    "chain_of_thought": [],
    "status": "IN_PROGRESS",
    "pr_url": None
}

print("=== RUNNING READER AGENT ===")
reader_output = reader_agent_node(mock_state)
mock_state.update(reader_output)

print("=== RUNNING NAVIGATOR AGENT ===")
nav_output = navigator_agent_node(mock_state)
mock_state.update(nav_output)

print("\n--- FINAL CHAIN OF THOUGHT ---")
for log in mock_state["chain_of_thought"]:
    print("-", log)

print("\nTarget Files Identified:", mock_state["target_files"])