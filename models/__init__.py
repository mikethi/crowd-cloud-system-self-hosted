"""Deterministic adaptive shard placement prototype.

This module plans minimal-change placement across peers with capacities and
failure domains. It does not discover peers or perform real network transfers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


SHARD_COUNT = 5


@dataclass(frozen=True)
class Peer:
    peer_id: str
    capacity: int
    failure_domain: str | None = None
    eligible: bool = True


@dataclass(frozen=True)
class PlacementPlan:
    desired_replicas: int
    placements: dict[int, tuple[str, ...]]
    additions: tuple[tuple[int, str], ...]
    removals: tuple[tuple[int, str], ...]
    under_replicated: tuple[int, ...]

    @property
    def placement_count(self) -> int:
        return sum(len(peers) for peers in self.placements.values())


def _target_replicas(peer_count: int, max_replicas: int) -> int:
    """Increase redundancy one tier per five eligible peers."""
    tier = 1 + max(0, (peer_count - 5) // 5)
    return min(max_replicas, tier)


def plan_placements(
    peers: Sequence[Peer],
    current: Mapping[int, Sequence[str]] | None = None,
    *,
    shard_count: int = SHARD_COUNT,
    max_replicas: int = 3,
) -> PlacementPlan:
    """Plan minimal-change shard placements within declared peer capacities."""
    if isinstance(shard_count, bool) or not isinstance(shard_count, int):
        raise ValueError("shard_count must be an integer")
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if isinstance(max_replicas, bool) or not isinstance(max_replicas, int):
        raise ValueError("max_replicas must be an integer")
    if max_replicas < 1:
        raise ValueError("max_replicas must be positive")

    by_id: dict[str, Peer] = {}
    for peer in peers:
        if (
            not isinstance(peer.peer_id, str)
            or not peer.peer_id
            or not peer.peer_id.strip()
        ):
            raise ValueError("peer_id must be a non-empty, non-whitespace string")
        if peer.peer_id in by_id:
            raise ValueError(f"duplicate peer_id: {peer.peer_id}")
        if isinstance(peer.capacity, bool) or not isinstance(peer.capacity, int):
            raise ValueError("peer capacity must be an integer")
        if peer.capacity < 0:
            raise ValueError("peer capacity cannot be negative")
        by_id[peer.peer_id] = peer

    eligible = {
        peer_id: peer
        for peer_id, peer in by_id.items()
        if peer.eligible and peer.capacity > 0
    }
    domains = {
        peer_id: peer.failure_domain or peer_id
        for peer_id, peer in eligible.items()
    }

    target = _target_replicas(len(eligible), max_replicas)
    current = current or {}

    for index in current:
        if (
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or index >= shard_count
        ):
            raise ValueError(f"current placement shard index out of range: {index!r}")

    assigned: dict[int, list[str]] = {index: [] for index in range(shard_count)}
    load = {peer_id: 0 for peer_id in eligible}

    for index in range(shard_count):
        seen_domains: set[str] = set()
        candidates = current.get(index, ())
        for peer_id in candidates:
            if not isinstance(peer_id, str) or peer_id not in eligible:
                continue
            if peer_id in assigned[index]:
                continue
            domain = domains[peer_id]
            if domain in seen_domains:
                continue
            if len(assigned[index]) >= target:
                break
            if load[peer_id] >= eligible[peer_id].capacity:
                continue

            assigned[index].append(peer_id)
            seen_domains.add(domain)
            load[peer_id] += 1

    for index in range(shard_count):
        while len(assigned[index]) < target:
            used_domains = {domains[p] for p in assigned[index]}
            candidates = [
                peer_id
                for peer_id, peer in eligible.items()
                if load[peer_id] < peer.capacity
                and peer_id not in assigned[index]
                and domains[peer_id] not in used_domains
            ]
            if not candidates:
                break

            chosen = min(
                candidates,
                key=lambda peer_id: (
                    load[peer_id] / eligible[peer_id].capacity,
                    load[peer_id],
                    peer_id,
                ),
            )
            assigned[index].append(chosen)
            load[chosen] += 1

    old_pairs = {
        (index, peer_id)
        for index, peer_ids in current.items()
        if isinstance(index, int) and not isinstance(index, bool)
        for peer_id in peer_ids
        if isinstance(peer_id, str)
    }
    new_pairs = {
        (index, peer_id)
        for index, peer_ids in assigned.items()
        for peer_id in peer_ids
    }

    return PlacementPlan(
        desired_replicas=target,
        placements={index: tuple(peer_ids) for index, peer_ids in assigned.items()},
        additions=tuple(sorted(new_pairs - old_pairs)),
        removals=tuple(sorted(old_pairs - new_pairs)),
        under_replicated=tuple(
            index for index, peer_ids in assigned.items() if len(peer_ids) < target
        ),
    )
