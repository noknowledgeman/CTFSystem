import socket

import httpx

from app.models.challenge_yaml import ServiceConfig


class ServiceChecker:
    """Runs service reachability checks locally on the admin VM.

    Targets are taken from the challenge.yaml service config (service.host),
    so challenges must declare a host reachable from the admin VM.
    """

    def check_service(self, service: ServiceConfig, timeout: int = 30) -> tuple[bool, str]:
        if service.protocol in {"tcp", "udp"}:
            return self._check_socket(service, timeout)
        if service.protocol in {"http", "https"}:
            return self._check_http(service, timeout)
        return False, f"Unsupported protocol: {service.protocol}"

    def _check_socket(self, service: ServiceConfig, timeout: int) -> tuple[bool, str]:
        target = f"{service.host}:{service.port}/{service.protocol}"
        sock_type = socket.SOCK_STREAM if service.protocol == "tcp" else socket.SOCK_DGRAM
        try:
            infos = socket.getaddrinfo(service.host, service.port, type=sock_type)
        except socket.gaierror as exc:
            return False, f"{target} resolve failed: {exc}"

        family, socktype, proto, _, sockaddr = infos[0]
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            if service.protocol == "tcp":
                sock.connect(sockaddr)
                return True, f"{target} reachable"
            # UDP has no handshake; a successful connect()+send only confirms
            # the host is routable, not that the port is open.
            sock.connect(sockaddr)
            sock.send(b"")
            return True, f"{target} routable (udp; port state not confirmable)"
        except OSError as exc:
            return False, f"{target} unreachable: {exc}"
        finally:
            sock.close()

    def _check_http(self, service: ServiceConfig, timeout: int) -> tuple[bool, str]:
        path = service.path or "/"
        url = f"{service.protocol}://{service.host}:{service.port}{path}"
        try:
            response = httpx.get(url, timeout=timeout, verify=False, follow_redirects=False)
        except httpx.HTTPError as exc:
            return False, f"url={url} expected={service.expected_status} request failed: {exc}"
        ok = response.status_code == service.expected_status
        return ok, f"url={url} expected={service.expected_status} got={response.status_code}"
