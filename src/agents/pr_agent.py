import os
from typing import Dict, Any
from github import Github
from src.state import BugResolverState

def pr_agent_node(state: BugResolverState) -> Dict[str, Any]:
    """Node that creates a GitHub branch, commits the fix, and opens a PR."""
    print("\n🚀 [PR Agent] Opening Pull Request on GitHub...")

    repo_owner = state.get("repo_owner")
    repo_name = state.get("repo_name")
    issue_number = state.get("issue_number")
    target_files = state.get("target_files", [])
    target_file = target_files[0] if target_files else "main.py"
    patched_code = state.get("patch_code", "")

    # Retrieve GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token or repo_owner == "test_owner":
        mock_pr_url = f"https://github.com/{repo_owner}/{repo_name}/pull/mock-1"
        print(f"⚠️ GITHUB_TOKEN missing or test repository detected. Skipped live PR creation.")
        print(f"   Simulated PR URL: {mock_pr_url}")
        
        chain_log = f"PR Agent simulated PR creation: {mock_pr_url}"
        return {
            "pr_url": mock_pr_url,
            "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
        }

    try:
        gh = Github(github_token)
        repo = gh.get_repo(f"{repo_owner}/{repo_name}")
        
        # 1. Get default branch (usually main or master)
        default_branch = repo.default_branch
        base_ref = repo.get_git_ref(f"heads/{default_branch}")
        
        # 2. Create new branch for the fix
        new_branch_name = f"fix/issue-{issue_number}"
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_ref.object.sha)

        # 3. Fetch file SHA and commit updated code
        file_contents = repo.get_contents(target_file, ref=default_branch)
        repo.update_file(
            path=target_file,
            message=f"fix: automated patch for issue #{issue_number}",
            content=patched_code,
            sha=file_contents.sha,
            branch=new_branch_name
        )

        # 4. Open Pull Request
        pr_title = f"fix: auto-resolve issue #{issue_number}"
        pr_body = (
            f"### Automated Bug Fix\n\n"
            f"Fixes #{issue_number}\n\n"
            f"**Changes:**\n"
            f"- Patched `{target_file}` to handle failing edge cases.\n"
            f"- Verified via automated sandbox test suite."
        )
        
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=new_branch_name,
            base=default_branch
        )

        print(f"✅ Pull Request successfully opened: {pr.html_url}")
        chain_log = f"PR Agent created Pull Request: {pr.html_url}"

        return {
            "pr_url": pr.html_url,
            "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
        }

    except Exception as e:
        print(f"❌ Failed to create PR: {str(e)}")
        chain_log = f"PR Agent failed to create PR: {str(e)}"
        return {
            "pr_url": None,
            "chain_of_thought": state.get("chain_of_thought", []) + [chain_log]
        }