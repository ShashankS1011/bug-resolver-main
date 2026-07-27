from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class BugResolverState(TypedDict):
    """
    Shared state schema passed between nodes in the LangGraph workflow.
    """
    # Input data
    repo_owner: str
    repo_name: str
    issue_number: int
    
    # Ingested context
    issue_title: str
    issue_body: str
    repo_files: List[str]            # File paths retrieved from repo
    target_files: List[str]          # Files identified as relevant by Navigator
    
    # Code & AST Context
    ast_summary: Dict[str, Any]      # Extracted functions/classes structure
    code_context: Dict[str, str]     # Path -> File content mapping
    
    # Proposed Solutions & Testing
    patch_code: Optional[str]        # Generated fix
    test_code: Optional[str]         # Generated Pytest code
    test_results: Optional[Dict[str, Any]] # Raw Pytest outputs from Docker
    
    # Workflow & Feedback Control
    iteration_count: int             # Tracks retry attempts when tests fail
    max_iterations: int              # Safety ceiling for retries
    chain_of_thought: List[str]      # Step-by-step reasoning logs
    status: str                      # Current status: 'IN_PROGRESS', 'PASSED', 'FAILED'
    pr_url: Optional[str]            # Final PR link if successful