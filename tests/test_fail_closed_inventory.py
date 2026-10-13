from __future__ import annotations

from typing import Any

from collectors import gh_inventory


class FakeResponse:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict[str, Any]]:
        return self._payload


class FakeClient:
    calls: list[dict[str, Any]] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, url: str, headers: dict[str, str], params: dict[str, Any]) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "params": params})
        if params["page"] == 1:
            return FakeResponse([
                {"id": 1, "name": "private-one", "full_name": "dhe-cruzer69/private-one",
                 "private": True, "owner": {"login": "dhe-cruzer69"}},
                {"id": 2, "name": "other", "full_name": "someone/other",
                 "private": True, "owner": {"login": "someone"}},
            ])
        return FakeResponse([])


def test_inventory_uses_authenticated_private_aware_endpoint(monkeypatch) -> None:
    FakeClient.calls = []
    monkeypatch.setattr(gh_inventory.httpx, "Client", FakeClient)
    repos = gh_inventory.list_repos("dhe-cruzer69", "test-token")

    assert len(repos) == 1
    assert repos[0]["full_name"] == "dhe-cruzer69/private-one"
    assert FakeClient.calls[0]["url"].endswith("/user/repos")
    assert FakeClient.calls[0]["params"]["affiliation"] == "owner,collaborator,organization_member"


def test_nightly_workflow_does_not_suppress_collector_or_push_failures() -> None:
    from pathlib import Path

    workflow = Path(".github/workflows/nightly-audit.yml").read_text(encoding="utf-8")
    assert "|| true" not in workflow
    assert "git push" in workflow
    assert "X4_FLEET_TOKEN" in workflow
