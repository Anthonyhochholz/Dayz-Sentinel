#!/usr/bin/env python3
"""API integration smoke test runner for DayZ Sentinel."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

import requests


@dataclass
class APITester:
    """Run a small set of integration checks against a running API."""

    base_url: str = "http://localhost:8000"
    passed: int = 0
    failed: int = 0
    failures: List[Tuple[str, str]] = field(default_factory=list)

    def _record(self, name: str, ok: bool, detail: str = "") -> None:
        symbol = "✓" if ok else "✗"
        print(f"{symbol} {name}")
        if detail:
            print(f"  → {detail}")
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append((name, detail))

    def _get(self, path: str, **kwargs):
        return requests.get(f"{self.base_url}{path}", timeout=10, **kwargs)

    def _post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", timeout=10, **kwargs)

    def check_health(self) -> None:
        try:
            response = self._get("/api/v1/health")
            self._record("GET /api/v1/health", response.status_code == 200, f"HTTP {response.status_code}")
        except Exception as exc:  # pragma: no cover - script runtime path
            self._record("GET /api/v1/health", False, str(exc))

    def check_items(self) -> None:
        try:
            response = self._get("/api/v1/economy/items", params={"limit": 5, "offset": 0})
            self._record("GET /api/v1/economy/items", response.status_code == 200, f"HTTP {response.status_code}")
        except Exception as exc:  # pragma: no cover - script runtime path
            self._record("GET /api/v1/economy/items", False, str(exc))

    def check_events(self) -> None:
        try:
            response = self._get("/api/v1/economy/events", params={"limit": 5, "offset": 0})
            self._record("GET /api/v1/economy/events", response.status_code == 200, f"HTTP {response.status_code}")
        except Exception as exc:  # pragma: no cover - script runtime path
            self._record("GET /api/v1/economy/events", False, str(exc))

    def check_toggle_event(self) -> None:
        try:
            events_response = self._get("/api/v1/economy/events", params={"limit": 1, "offset": 0})
            if events_response.status_code != 200:
                self._record("POST /api/v1/economy/events/{event}/toggle-active", False, f"HTTP {events_response.status_code}")
                return

            events = events_response.json().get("data", [])
            if not events:
                self._record("POST /api/v1/economy/events/{event}/toggle-active", False, "No event found")
                return

            event_name = events[0].get("event_name")
            toggle_response = self._post(f"/api/v1/economy/events/{event_name}/toggle-active")
            self._record(
                "POST /api/v1/economy/events/{event}/toggle-active",
                toggle_response.status_code == 200,
                f"HTTP {toggle_response.status_code}",
            )
        except Exception as exc:  # pragma: no cover - script runtime path
            self._record("POST /api/v1/economy/events/{event}/toggle-active", False, str(exc))

    def run(self) -> int:
        print("#" * 60)
        print("DayZ Sentinel API Integration Smoke Test")
        print("#" * 60)

        self.check_health()
        self.check_items()
        self.check_events()
        self.check_toggle_event()

        total = self.passed + self.failed
        print("\nSummary")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total: {total}")
        print(f"Finished: {datetime.now():%Y-%m-%d %H:%M:%S}")

        if self.failures:
            print("\nFailures:")
            for name, detail in self.failures:
                print(f"- {name}: {detail}")

        return 0 if self.failed == 0 else 1


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    return APITester(base_url=base_url).run()


if __name__ == "__main__":
    raise SystemExit(main())
