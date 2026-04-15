from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import paramiko


@dataclass
class RemoteCommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SSHService:
    def __init__(
        self,
        username: str,
        private_key_path: str,
        connect_timeout: int = 15,
        command_timeout: int = 60,
    ) -> None:
        self.username = username
        self.private_key_path = str(Path(private_key_path).expanduser())
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout

    def run_command(self, host: str, command: str, timeout: int | None = None) -> RemoteCommandResult:
        with self._client(host) as client:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout or self.command_timeout)
            _ = stdin
            exit_code = stdout.channel.recv_exit_status()
            return RemoteCommandResult(
                command=command,
                exit_code=exit_code,
                stdout=stdout.read().decode("utf-8", errors="replace"),
                stderr=stderr.read().decode("utf-8", errors="replace"),
            )

    def upload_file(self, host: str, local_path: str, remote_path: str) -> None:
        with self._client(host) as client:
            with client.open_sftp() as sftp:
                sftp.put(local_path, remote_path)

    def _client(self, host: str) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key = paramiko.Ed25519Key.from_private_key_file(self.private_key_path)
        client.connect(
            hostname=host,
            username=self.username,
            pkey=key,
            timeout=self.connect_timeout,
            banner_timeout=self.connect_timeout,
            auth_timeout=self.connect_timeout,
        )
        return client
