from src.agents.investigator_agents import reader_agent_node, navigator_agent_node
from src.agents.developer_agents import developer_agent_node, tester_agent_node
from src.state import BugResolverState

mock_state: BugResolverState = {
    "repo_owner": "test_owner",
    "repo_name": "test_repo",
    "issue_number": 1,
    "issue_title": "Division by zero crash in calculate_average",
    "issue_body": "When providing an empty list to calculate_average(), the system throws ZeroDivisionError instead of returning 0.0.",
    "repo_files": ["math_ops/stats.py"],
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

# 1. Investigate
mock_state.update(reader_agent_node(mock_state))
mock_state.update(navigator_agent_node(mock_state))

# 2. Develop Fix & Test
mock_state.update(developer_agent_node(mock_state))

print("\n--- GENERATED PATCH CODE ---")
print(mock_state["patch_code"])

print("\n--- GENERATED TEST CODE ---")
print(mock_state["test_code"])

# 3. Execute in Sandbox
mock_state.update(tester_agent_node(mock_state))

print("\n--- SANDBOX TEST RESULT ---")
print("Status:", mock_state["status"])
print("Passed:", mock_state["test_results"]["passed"])
print("Pytest Output:\n", mock_state["test_results"]["output"])