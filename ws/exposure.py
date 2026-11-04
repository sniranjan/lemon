"""Counts how often each word or number has appeared, and in what role."""

from __future__ import annotations

from collections import Counter, defaultdict


class ExposureTracker:
    """Roles are e.g. "new", "strip", "grid", "story", "count"."""

    def __init__(self) -> None:
        self._by_role: dict[str, Counter[str]] = defaultdict(Counter)
        self._new_on: dict[str, int] = {}

    def add(self, item: str, role: str, page: int | None = None) -> None:
        if role == "new":
            if item in self._new_on:
                raise ValueError(f"{item!r} is already new on page {self._new_on[item]}")
            if page is not None:
                self._new_on[item] = page
        self._by_role[role][item] += 1

    def total(self, item: str) -> int:
        return sum(c[item] for c in self._by_role.values())

    def count(self, item: str, role: str) -> int:
        return self._by_role[role][item]

    def new_on(self, item: str) -> int | None:
        return self._new_on.get(item)

    def items(self) -> set[str]:
        return {i for c in self._by_role.values() for i in c}
