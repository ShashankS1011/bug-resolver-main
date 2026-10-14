import docker
import os
import tempfile
import subprocess
import sys
from pathlib import PurePath
from typing import Any, Dict

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

    @staticmethod
    def _write_files(temp_dir: str, code_files: Dict[str, str], test_code: str) -> str:
        """Write sandbox inputs while preventing writes outside the temp directory."""
        for file_path, content in code_files.items():
            # Normalize both separators so validation is consistent on Windows and Linux.
            relative_path = PurePath(file_path.replace("\\", "/"))
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"Unsafe sandbox path: {file_path!r}")

            full_path = os.path.join(temp_dir, *relative_path.parts)
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        test_file_path = os.path.join(temp_dir, "test_solution.py")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        return test_file_path

    def _run_docker(self, code_files: Dict[str, str], test_code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                self._write_files(temp_dir, code_files, test_code)
                # Runs python -m unittest or pre-installed pytest inside the container
                container_output = self.client.containers.run(
                    image=self.image,
                    command="sh -c 'python -m pip install pytest >/dev/null 2>&1 && pytest /workspace/test_solution.py -v'",
                    volumes={temp_dir: {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    remove=True,
                    network_disabled=False,  # Set to False so pip install works
                    mem_limit="512m"
                )
                return {"passed": True, "exit_code": 0, "output": container_output.decode("utf-8")}
            except docker.errors.ContainerError as ce:
                # Safely extract Pytest failure output from stderr or stdout
                output = ""
                if hasattr(ce, "stdout") and ce.stdout:
                    output = ce.stdout.decode("utf-8")
                elif hasattr(ce, "stderr") and ce.stderr:
                    output = ce.stderr.decode("utf-8")
                else:
                    output = str(ce)
                
                return {"passed": False, "exit_code": ce.exit_code, "output": output}
            except (OSError, ValueError) as exc:
                return {"passed": False, "exit_code": -1, "output": f"Sandbox setup error: {exc}"}

    def _run_local_fallback(self, code_files: Dict[str, str], test_code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                self._write_files(temp_dir, code_files, test_code)
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
            except (OSError, ValueError, subprocess.TimeoutExpired) as e:
                return {
                    "passed": False,
                    "exit_code": -1,
                    "output": f"Local sandbox error: {str(e)}"
                }
