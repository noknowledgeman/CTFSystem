from pathlib import Path

from app.models.challenge_yaml import VerifyConfig
from app.services.ssh_service import SSHService


class ScriptRunner:
    def __init__(self, ssh: SSHService, default_timeout: int = 30) -> None:
        self.ssh = ssh
        self.default_timeout = default_timeout

    def run_verify_script(self, host: str, local_root: Path, verify: VerifyConfig, expected_flag: str) -> tuple[bool, str]:
        local_script = local_root / verify.script
        remote_script = f"/tmp/{local_script.name}"
        self.ssh.upload_file(host, str(local_script), remote_script)
        self.ssh.run_command(host, f"chmod +x {remote_script}")

        timeout = verify.timeout or self.default_timeout
        if verify.language == "python":
            command = f"python3 {remote_script}"
        else:
            command = f"bash {remote_script}"

        result = self.ssh.run_command(host, command, timeout=timeout)
        output = (result.stdout + "\n" + result.stderr).strip()
        ok = result.exit_code == 0 and expected_flag in output
        return ok, output
