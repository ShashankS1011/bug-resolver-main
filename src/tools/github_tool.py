import os
from typing import Dict, Any, List
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

class GitHubTool:
    def __init__(self, token: str = None):
        # Uses GITHUB_TOKEN from .env if not explicitly passed
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.gh = Github(auth=Auth.Token(self.token)) if self.token else Github()

    def fetch_issue_details(self, owner: str, repo_name: str, issue_num: int) -> Dict[str, Any]:
        """Fetches the title, description body, and existing comments of an issue."""
        repo = self.gh.get_repo(f"{owner}/{repo_name}")
        issue = repo.get_issue(number=issue_num)
        
        comments = [c.body for c in issue.get_comments()]
        
        return {
            "title": issue.title,
            "body": issue.body or "",
            "comments": comments,
            "author": issue.user.login,
            "labels": [label.name for label in issue.labels]
        }

    def list_repository_files(self, owner: str, repo_name: str, extension: str = ".py") -> List[str]:
        """Recursively lists all files in the repository matching the given extension."""
        repo = self.gh.get_repo(f"{owner}/{repo_name}")
        tree = repo.get_git_tree(repo.default_branch, recursive=True)
        
        return [
            item.path for item in tree.tree 
            if item.type == "blob" and item.path.endswith(extension)
        ]

    def get_file_content(self, owner: str, repo_name: str, file_path: str) -> str:
        """Retrieves raw string content for a specific file path."""
        repo = self.gh.get_repo(f"{owner}/{repo_name}")
        content_file = repo.get_contents(file_path)
        return content_file.decoded_content.decode("utf-8")