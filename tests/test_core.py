import pytest

from src.agents.developer_agents import parse_developer_output
from src.agents.investigator_agents import _parse_json_response
from src.graph import should_continue
from src.tools.ast_tool import parse_code_structure
from src.tools.docker_sandbox import DockerSandbox


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
