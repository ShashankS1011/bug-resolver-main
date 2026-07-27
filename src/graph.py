from typing import Literal
from langgraph.graph import StateGraph, END
from src.state import BugResolverState
from src.agents.investigator_agents import reader_agent_node, navigator_agent_node
from src.agents.developer_agents import developer_agent_node, tester_agent_node
from src.agents.pr_agent import pr_agent_node


def should_continue(state: BugResolverState) -> Literal["developer", "pr_agent", END]:
    """Conditional routing logic: decides whether to retry, create PR, or finish."""
    status = state.get("status")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)

    if status == "PASSED":
        print("\n🎉 [Graph Router] Tests passed! Proceeding to PR Agent.")
        return "pr_agent"

    if iteration_count >= max_iterations:
        print(f"\n⚠️ [Graph Router] Reached max iterations ({max_iterations}). Stopping.")
        return END

    print(f"\n🔄 [Graph Router] Tests failed or in progress. Retrying (Attempt {iteration_count + 1}/{max_iterations})...")
    return "developer"


def build_bug_resolver_graph():
    """Constructs and compiles the multi-agent LangGraph workflow."""
    workflow = StateGraph(BugResolverState)

    # 1. Add Agent Nodes
    workflow.add_node("reader", reader_agent_node)
    workflow.add_node("navigator", navigator_agent_node)
    workflow.add_node("developer", developer_agent_node)
    workflow.add_node("tester", tester_agent_node)
    workflow.add_node("pr_agent", pr_agent_node)

    # 2. Define Linear Flow: Reader -> Navigator -> Developer -> Tester
    workflow.set_entry_point("reader")
    workflow.add_edge("reader", "navigator")
    workflow.add_edge("navigator", "developer")
    workflow.add_edge("developer", "tester")

    # 3. Add Conditional Edge: Tester -> PR Agent (if passed) or Developer (retry) or END
    workflow.add_conditional_edges(
        "tester",
        should_continue,
        {
            "developer": "developer",
            "pr_agent": "pr_agent",
            END: END
        }
    )

    # 4. PR Agent completes the workflow
    workflow.add_edge("pr_agent", END)

    return workflow.compile()