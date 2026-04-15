from app.services.ssh_service import SSHService


class DockerChecker:
    def __init__(self, ssh: SSHService) -> None:
        self.ssh = ssh

    def check_containers_running(self, host: str, remote_dir: str) -> tuple[bool, str]:
        cmd = f"cd {remote_dir} && (docker compose ps --status running || docker-compose ps)"
        result = self.ssh.run_command(host, cmd)
        ok = result.exit_code == 0 and ("running" in result.stdout.lower() or "up" in result.stdout.lower())
        details = (result.stdout + "\n" + result.stderr).strip()
        return ok, details

    def check_port_listening(self, host: str, port: int) -> tuple[bool, str]:
        cmd = f"ss -tln | grep -E ':{port}\\s' || netstat -tln | grep -E ':{port}\\s'"
        result = self.ssh.run_command(host, cmd)
        ok = result.exit_code == 0
        details = (result.stdout + "\n" + result.stderr).strip()
        return ok, details
