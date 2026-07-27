from src.graph import build_bug_resolver_graph
from src.state import BugResolverState

app = build_bug_resolver_graph()

YOUR_USERNAME = "ShashankS1011"

initial_state: BugResolverState = {
    "repo_owner": YOUR_USERNAME,
    "repo_name": "bug-resolver",
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

print(f"🚀 Starting LangGraph Bug Resolver against live repo '{YOUR_USERNAME}/bug-resolver'...\n")
final_state = app.invoke(initial_state)

print("\n================ FINAL REPORT ================")
print(f"Status: {final_state['status']}")
print(f"Iterations: {final_state['iteration_count']}")
print(f"PR URL: {final_state.get('pr_url')}")
print("\n--- Patched Code ---")
print(final_state.get("patch_code"))
print("\n--- Chain of Thought ---")
for log in final_state["chain_of_thought"]:
    print("-", log)