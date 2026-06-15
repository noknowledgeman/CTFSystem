import subprocess
from pathlib import Path

from app.models.challenge_yaml import VerifyConfig


class ScriptRunner:
    def __init__(self, default_timeout: int = 30) -> None:
        self.default_timeout = default_timeout

    def install_dependencies(self, verify: VerifyConfig, timeout: int):
        if not verify.dependencies:
            return
        if verify.language == "python":
            cmd = ["pip3", "install", *verify.dependencies]
        else:
            cmd = ["apt-get", "install", "-y", *verify.dependencies]
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def run_verify_script(self, local_root: Path, verify: VerifyConfig) -> tuple[bool, str]:
        local_script = local_root / verify.script

        timeout = verify.timeout or self.default_timeout
        self.install_dependencies(verify, timeout)

        interpreter = "python3" if verify.language == "python" else "bash"
        result = subprocess.run(
            [interpreter, str(local_script)],
            cwd=str(local_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        ok = result.returncode == 0
        return ok, output
