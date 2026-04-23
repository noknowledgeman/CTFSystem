from app.models.challenge_yaml import ServiceConfig
from app.services.ssh_service import SSHService


class ServiceChecker:
    def __init__(self, ssh: SSHService) -> None:
        self.ssh = ssh

    def check_service(self, host: str, service: ServiceConfig, timeout: int = 30) -> tuple[bool, str]:
        if service.protocol in {"tcp", "udp"}:
            return self._check_socket(host, service, timeout)
        if service.protocol in {"http", "https"}:
            return self._check_http(host, service, timeout)
        return False, f"Unsupported protocol: {service.protocol}"

    def _check_socket(self, host: str, service: ServiceConfig, timeout: int) -> tuple[bool, str]:
        flag = "-tln" if service.protocol == "tcp" else "-uln"
        cmd = (
            f"ss {flag} | grep -E ':{service.port}\\s' "
            f"|| netstat {flag} | grep -E ':{service.port}\\s'"
        )
        result = self.ssh.run_command(host, cmd, timeout=timeout)
        details = (result.stdout + "\n" + result.stderr).strip()
        return result.exit_code == 0, details

    def _check_http(self, host: str, service: ServiceConfig, timeout: int) -> tuple[bool, str]:
        path = service.path or "/"
        scheme = service.protocol
        url = f"{scheme}://{service.host}:{service.port}{path}"
        cmd = f"curl -ksS -o /dev/null -w '%{{http_code}}' --max-time {timeout} '{url}'"
        result = self.ssh.run_command(host, cmd, timeout=timeout)
        code = result.stdout.strip()
        ok = result.exit_code == 0 and code == str(service.expected_status)
        details = f"url={url} expected={service.expected_status} got={code or 'n/a'} stderr={result.stderr.strip()}"
        return ok, details
