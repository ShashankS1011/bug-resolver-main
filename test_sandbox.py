from src.tools.docker_sandbox import DockerSandbox

sandbox = DockerSandbox()

# Sample target code and test
code_files = {
    "math_utils.py": "def multiply(a, b):\n    return a * b\n"
}

test_code = """
from math_utils import multiply

def test_multiply():
    assert multiply(3, 4) == 12
"""

print("Running sandbox test...")
result = sandbox.run_tests_in_sandbox(code_files, test_code)
print("Passed:", result["passed"])
print("Output:\n", result["output"])