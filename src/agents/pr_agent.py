import os
import uuid
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from github import Auth, Github, GithubException

from src.state import BugResolverState

load_dotenv()


MAX_BRANCH_ATTEMPTS = 5


def _result(state: BugResolverState, *, pr_url: Optional[str], status: str, message: str) -> Dict[str, Any]:
    """Build a consistent state update for successful and failed PR runs."""
    return {
        "pr_url": pr_url,
        "status": status,
        "pr_error": None if status == "PASSED" else message,
        "chain_of_thought": state.get("chain_of_thought", []) + [message],
    }


def _validate_inputs(state: BugResolverState) -> tuple[str, str, int, str, str]:
    """Validate the minimum data needed before making any GitHub changes."""
    repo_owner = state.get("repo_owner")
    repo_name = state.get("repo_name")
    issue_number = state.get("issue_number")
    target_files = state.get("target_files") or []
    patched_code = state.get("patch_code")

    if not isinstance(repo_owner, str) or not repo_owner.strip():
        raise ValueError("repo_owner is required")
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("repo_name is required")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ValueError("issue_number must be a positive integer")
    if len(target_files) != 1 or not isinstance(target_files[0], str) or not target_files[0].strip():
        raise ValueError("exactly one target file is required")
    target_file = target_files[0].replace("\\", "/")
    path_parts = target_file.split("/")
    if target_file.startswith("/") or ".." in path_parts:
        raise ValueError("target file must be a repository-relative path")
    if not isinstance(patched_code, str) or not patched_code.strip():
        raise ValueError("patch_code must contain non-empty code")

    return repo_owner.strip(), repo_name.strip(), issue_number, target_file, patched_code


def _create_branch(repo: Any, commit_sha: str, issue_number: int) -> str:
    """Create a unique fix branch, retrying only when GitHub reports a collision."""
    for _ in range(MAX_BRANCH_ATTEMPTS):
        branch_name = f"fix/issue-{issue_number}-{uuid.uuid4().hex[:12]}"
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=commit_sha)
            return branch_name
        except GithubException as error:
            if error.status != 422:
                raise
    raise RuntimeError("could not create a unique GitHub branch after several attempts")


def pr_agent_node(state: BugResolverState) -> Dict[str, Any]:
    """Create a branch, commit the validated patch, and open a pull request."""
    print("\n[PR Agent] Creating remote branch and submitting Pull Request...")

    try:
        repo_owner, repo_name, issue_number, target_file, patched_code = _validate_inputs(state)
    except ValueError as error:
        message = f"PR Agent rejected input: {error}"
        print(f"[Error] {message}")
        return _result(state, pr_url=None, status="FAILED", message=message)

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        message = "PR Agent could not create a live PR: GITHUB_TOKEN is not configured."
        print(f"[Error] {message}")
        return _result(state, pr_url=None, status="FAILED", message=message)

    repo = None
    branch_name = None
    try:
        github = Github(auth=Auth.Token(github_token))
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        default_branch = repo.default_branch
        base_ref = repo.get_git_ref(f"heads/{default_branch}")

        file_contents = repo.get_contents(target_file, ref=default_branch)
        if isinstance(file_contents, list):
            raise ValueError(f"target path is a directory, not a file: {target_file}")

        branch_name = _create_branch(repo, base_ref.object.sha, issue_number)
        repo.update_file(
            path=target_file,
            message=f"fix: automated patch for issue #{issue_number}",
            content=patched_code,
            sha=file_contents.sha,
            branch=branch_name,
        )

        pr = repo.create_pull(
            title=f"fix: auto-resolve issue #{issue_number}",
            body=(
                "### Automated Bug Fix\n\n"
                f"Fixes #{issue_number}\n\n"
                "**Changes:**\n"
                f"- Patched `{target_file}`.\n"
                "- Verified by the automated sandbox test suite."
            ),
            head=branch_name,
            base=default_branch,
        )
        message = f"PR Agent created Pull Request: {pr.html_url}"
        print(f"[Success] Pull Request published: {pr.html_url}")
        return _result(state, pr_url=pr.html_url, status="PASSED", message=message)
    except Exception as error:
        message = f"PR Agent failed to create PR: {error}"
        print(f"[Error] {message}")
        if repo is not None and branch_name is not None:
            try:
                repo.get_git_ref(f"heads/{branch_name}").delete()
            except Exception as cleanup_error:
                print(f"[Warning] Could not clean up branch {branch_name}: {cleanup_error}")
        return _result(state, pr_url=None, status="FAILED", message=message)
