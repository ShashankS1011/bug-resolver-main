from unittest.mock import Mock, patch

import pytest

from src.agents.developer_agents import parse_developer_output
from src.agents.investigator_agents import _parse_json_response
from src.agents.pr_agent import pr_agent_node
from src.graph import should_continue
from src.tools.ast_tool import parse_code_structure
from src.tools.docker_sandbox import DockerSandbox


def _pr_state(**overrides):
    state = {
        "repo_owner": "owner",
        "repo_name": "repo",
        "issue_number": 42,
        "target_files": ["src/app.py"],
        "patch_code": "def fixed():\n    return True\n",
    }
    state.update(overrides)
    return state


def test_parse_code_structure_includes_async_functions_and_class_methods():
    summary = parse_code_structure(
        "async def load(value):\n"
        "    return value\n\n"
        "class Service:\n"
        "    async def run(self, value):\n"
        "        return value\n"
    )

    assert summary["functions"][0]["name"] == "load"
    assert summary["classes"][0]["methods"][0]["name"] == "run"
    assert summary["classes"][0]["methods"][0]["args"] == ["self", "value"]


def test_parse_code_structure_reports_syntax_errors():
    result = parse_code_structure("def broken(:\n")

    assert "error" in result
    assert "SyntaxError" in result["error"]


def test_developer_output_supports_python_fenced_blocks():
    result = parse_developer_output(
        "```PYTHON\nx = 1\n```\n\n```py\ndef test_value():\n    assert 1 == 1\n```"
    )

    assert result["patched_code"] == "x = 1"
    assert "test_value" in result["test_code"]


def test_json_response_removes_only_markdown_fence():
    assert _parse_json_response('```json\n{"target_files": ["src/app.py"]}\n```') == {
        "target_files": ["src/app.py"]
    }


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"status": "PASSED", "iteration_count": 1, "max_iterations": 3}, "pr_agent"),
        ({"status": "FAILED", "iteration_count": 3, "max_iterations": 3}, "__end__"),
        ({"status": "FAILED", "iteration_count": 0, "max_iterations": 3}, "developer"),
    ],
)
def test_should_continue_routes_workflow(state, expected):
    assert should_continue(state) == expected


def test_sandbox_runs_root_level_files_without_creating_empty_directory():
    sandbox = DockerSandbox.__new__(DockerSandbox)
    result = sandbox._run_local_fallback(
        {"math_utils.py": "def multiply(a, b):\n    return a * b\n"},
        "from math_utils import multiply\n\n"
        "def test_multiply():\n"
        "    assert multiply(3, 4) == 12\n",
    )

    assert result["passed"] is True


def test_sandbox_rejects_path_traversal():
    sandbox = DockerSandbox.__new__(DockerSandbox)

    with pytest.raises(ValueError, match="Unsafe sandbox path"):
        sandbox._write_files("C:\\temp", {"..\\outside.py": "raise RuntimeError"}, "")


def test_pr_agent_rejects_missing_token_without_fake_success(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    result = pr_agent_node(
        {
            "repo_owner": "owner",
            "repo_name": "repo",
            "issue_number": 1,
            "target_files": ["src/app.py"],
            "patch_code": "return 1",
        }
    )

    assert result["pr_url"] is None
    assert result["status"] == "FAILED"
    assert "GITHUB_TOKEN" in result["pr_error"]


def test_pr_agent_rejects_empty_patch_before_authentication(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token")

    result = pr_agent_node(
        {
            "repo_owner": "owner",
            "repo_name": "repo",
            "issue_number": 1,
            "target_files": ["src/app.py"],
            "patch_code": "",
        }
    )

    assert result["status"] == "FAILED"
    assert "patch_code" in result["pr_error"]


@patch("src.agents.pr_agent.Github")
def test_pr_agent_creates_branch_commit_and_pull_request(github_class, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    repo = Mock()
    repo.default_branch = "main"
    repo.get_git_ref.return_value.object.sha = "base-sha"
    repo.get_contents.return_value.sha = "file-sha"
    repo.create_pull.return_value.html_url = "https://github.com/owner/repo/pull/7"
    github_class.return_value.get_repo.return_value = repo

    result = pr_agent_node(_pr_state())

    assert result["status"] == "PASSED"
    assert result["pr_url"] == "https://github.com/owner/repo/pull/7"
    repo.update_file.assert_called_once()
    repo.create_pull.assert_called_once()
    assert repo.create_pull.call_args.kwargs["base"] == "main"
    assert github_class.call_args.kwargs["auth"] is not None


@patch("src.agents.pr_agent.Github")
def test_pr_agent_cleans_up_branch_when_pull_request_fails(github_class, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    repo = Mock()
    repo.default_branch = "main"
    repo.get_git_ref.return_value.object.sha = "base-sha"
    repo.get_contents.return_value.sha = "file-sha"
    repo.create_pull.side_effect = RuntimeError("pull request rejected")
    github_class.return_value.get_repo.return_value = repo

    result = pr_agent_node(_pr_state())

    assert result["status"] == "FAILED"
    assert "pull request rejected" in result["pr_error"]
    repo.get_git_ref.return_value.delete.assert_called_once()
