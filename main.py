"""Wallet state used by the Crowd-Cloud System self-hosting prototype."""
from __future__ import annotations

import math
import time
import uuid
from typing import Dict, List, Optional

GOOGLPLEX = 10**100


class Wallet:
    """Minimal wallet model with resource accounting and pricing."""

    def __init__(
        self,
        wallet_id: str,
        is_master: bool = False,
        parent: Optional["Wallet"] = None,
    ) -> None:
        self.wallet_id = wallet_id
        self.is_master = is_master
        self.parent = parent
        self.children: List[Wallet] = []
        self.creation_time = time.time()
        self.master_count = 1.0
        self.lifetime = 3600 * 24 * 30
        self.self_destruct_triggers: List[float] = []
        self.invited_wallets: Dict[str, str] = {}
        self.is_publicly_paid = False
        self.origin_hash = wallet_id
        self.cooldown_end = 0.0
        self.provence_chain: List[Dict] = []
        self.fifo_work_owed: List[Dict] = []

        self.hdd_share_bytes = 0.0
        self.cpu_cycles = 0.0
        self.memory_mb = 0.0
        self.shared_hdd: Dict[str, float] = {}
        self.shared_cpu: Dict[str, float] = {}
        self.shared_memory: Dict[str, float] = {}

    def add_child(self, child_wallet: "Wallet") -> None:
        self.children.append(child_wallet)
        child_wallet.parent = self
        self.aggregate_resources()

    def aggregate_resources(self) -> tuple[float, float, float]:
        total_hdd = self.hdd_share_bytes
        total_cpu = self.cpu_cycles
        total_mem = self.memory_mb

        for child in self.children:
            child_hdd, child_cpu, child_mem = child.aggregate_resources()
            total_hdd += child_hdd
            total_cpu += child_cpu
            total_mem += child_mem

        self.master_count = total_hdd + total_cpu + total_mem
        return total_hdd, total_cpu, total_mem

    def share_resource(self, peer_wallet_id: str, resource_type: str, amount: float) -> None:
        if resource_type not in {"hdd", "cpu", "memory"}:
            raise ValueError(f"Unsupported resource type: {resource_type!r}")
        if not isinstance(peer_wallet_id, str) or not peer_wallet_id:
            raise ValueError("peer_wallet_id must be a non-empty string")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError("amount must be a finite positive number")
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("amount must be finite and greater than zero")

        maps = {
            "hdd": (self.shared_hdd, "hdd_share_bytes"),
            "cpu": (self.shared_cpu, "cpu_cycles"),
            "memory": (self.shared_memory, "memory_mb"),
        }
        peer_map, total_attr = maps[resource_type]
        if peer_wallet_id in peer_map:
            raise ValueError(f"Duplicate {resource_type} contribution from {peer_wallet_id!r}")

        peer_map[peer_wallet_id] = amount
        setattr(self, total_attr, getattr(self, total_attr) + amount)

    def mark_publicly_paid(self) -> None:
        self.is_publicly_paid = True
        self.provence_chain.append(
            {
                "time": time.time(),
                "action": "publicly_paid",
                "delta": 0,
                "shared_resources": {
                    "hdd": self.hdd_share_bytes / GOOGLPLEX,
                    "cpu": self.cpu_cycles / GOOGLPLEX,
                    "memory": self.memory_mb / GOOGLPLEX,
                },
            }
        )

    def add_work_owed(self, amount, creditor) -> None:
        self.fifo_work_owed.append({"amount": amount, "creditor": creditor, "time": time.time()})

    def process_reciprocal_repayment(self) -> None:
        for owed in self.fifo_work_owed[:]:
            if time.time() > owed["time"] + 86400:
                repayment = owed["amount"] * 0.15
                owed["creditor"].master_count += repayment
                self.master_count -= repayment
                self.fifo_work_owed.remove(owed)

    def can_access(self, requester_id: str) -> bool:
        if self.self_destruct_triggers and time.time() > max(self.self_destruct_triggers):
            return requester_id in self.invited_wallets and self.invited_wallets[requester_id]
        return True

    def self_destruct(self) -> None:
        self.self_destruct_triggers.append(time.time())

    def announce_to_dht(self, resource_type: str) -> None:
        print(f"[{self.wallet_id}] Announcing {resource_type} share to Kademlia DHT")

    def discover_peers(self, resource_type: str) -> None:
        print(f"[{self.wallet_id}] Discovering peers with {resource_type} via DHT")

    def create_ppm_transaction(self, direction: str, resource_type: str = "hdd") -> Dict:
        if direction not in ("enter", "exit"):
            raise ValueError("direction must be 'enter' or 'exit'")
        if resource_type not in ("hdd", "cpu", "memory"):
            raise ValueError("unsupported resource_type")

        ppm = self.calculate_real_time_ppm()
        if not isinstance(ppm, (int, float)) or not math.isfinite(ppm) or ppm < 0:
            raise ValueError("calculated PPM must be finite and nonnegative")

        return {
            "transaction_id": str(uuid.uuid4()),
            "wallet_id": self.wallet_id,
            "direction": direction,
            "resource_type": resource_type,
            "ppm": ppm,
            "amount": 1,
            "timestamp": time.time(),
        }

    def calculate_real_time_ppm(self) -> float:
        base_ppm = self.master_count * 0.5
        resource_factor = (
            (self.hdd_share_bytes / GOOGLPLEX)
            + (self.cpu_cycles / GOOGLPLEX)
            + (self.memory_mb / GOOGLPLEX)
        )
        return base_ppm * resource_factor
