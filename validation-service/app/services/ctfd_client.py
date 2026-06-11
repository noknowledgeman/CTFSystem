from __future__ import annotations

import httpx

from app.models.challenge_yaml import ChallengeYaml


class CTFdClient:
    def __init__(self, base_url: str, api_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Token {self.api_token}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self._headers,
                json=payload,
            )
        response.raise_for_status()
        return response.json()

    def ensure_challenge(self, challenge: ChallengeYaml, category: str = "Automated Validation") -> int:
        existing = self._request("GET", "/api/v1/challenges")
        for item in existing.get("data", []):
            if item.get("name") == challenge.name:
                return int(item["id"])

        payload = {
            "name": challenge.name,
            "description": challenge.description,
            "value": self._points_from_difficulty(challenge.difficulty),
            "category": category,
            "type": "standard",
            "state": "visible",
        }
        created = self._request("POST", "/api/v1/challenges", payload=payload)
        challenge_id = int(created["data"]["id"])
        self.set_flag(challenge_id, challenge.flag)
        return challenge_id

    def set_flag(self, challenge_id: int, flag: str) -> dict:
        payload = {"challenge_id": challenge_id, "content": flag, "type": "static", "data": ""}
        return self._request("POST", "/api/v1/flags", payload=payload)

    def _points_from_difficulty(self, difficulty: str) -> int:
        mapping = {"simple": 100, "medium": 250, "difficult": 500}
        return mapping.get(difficulty, 150)
