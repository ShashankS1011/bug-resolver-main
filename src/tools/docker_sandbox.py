import docker
import os
import tempfile
import subprocess
import sys
from typing import Dict, Any

class DockerSandbox:
    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        self.use_docker = True
        try:
            self.client = docker.from_env()
            self.client.ping()  # Test connection to Docker daemon
        except Exception as e:
            self.client = None
            self.use_docker = False
            print("[Info] Docker unavailable. Falling back to local temporary subprocess sandbox.")

    def run_tests_in_sandbox(self, code_files: Dict[str, str], test_code: str) -> Dict[str, Any]:
        """
        Executes code and tests. Uses Docker if available, otherwise falls back to local subprocess.
        """
        if self.use_docker:
            return self._run_docker(code_files, test_code)
        else:
            return self._run_local_fallback(code_files, test_code)

    def _run_docker(self, code_files: Dict[str, str], test_code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            for file_path, content in code_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            test_file_path = os.path.join(temp_dir, "test_solution.py")
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            try:
                container_output = self.client.containers.run(
                    image=self.image,
                    command="sh -c 'pip install pytest && pytest /workspace/test_solution.py -v'",
                    volumes={temp_dir: {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    remove=True,
                    network_disabled=True,
                    mem_limit="512m"
                )
                return {"passed": True, "exit_code": 0, "output": container_output.decode("utf-8")}
            except docker.errors.ContainerError as ce:
                output = ce.stderr.decode("utf-8") if ce.stderr else ce.stdout.decode("utf-8")
                return {"passed": False, "exit_code": ce.exit_code, "output": output}

    def _run_local_fallback(self, code_files: Dict[str, str], test_code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write python source files
            for file_path, content in code_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Write test file
            test_file_path = os.path.join(temp_dir, "test_solution.py")
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            # Run pytest via subprocess in temp directory
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "test_solution.py", "-v"],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                passed = (result.returncode == 0)
                output = result.stdout if result.stdout else result.stderr
                return {
                    "passed": passed,
                    "exit_code": result.returncode,
                    "output": output
                }
            except Exception as e:
                return {
                    "passed": False,
                    "exit_code": -1,
                    "output": f"Local sandbox error: {str(e)}"
                }