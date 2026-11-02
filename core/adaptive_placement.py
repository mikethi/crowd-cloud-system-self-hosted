"""Threshold-based source sharding using systematic Reed-Solomon coding.

This module split source bytes into 3 data shards plus 2 parity shards and can
reassemble valid source code from any three valid shard records. It focuses on
code persistence and recovery, not blockchain consensus or external peer
verification.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Sequence


class ChainShardManager:
    """Split source bytes into 3 data shards plus 2 parity shards."""

    DATA_SHARDS = 3
    TOTAL_SHARDS = 5
    SCHEME = "rs-gf256-systematic-v1"

    def __init__(
        self,
        redundancy_threshold: int = 3,
        total_shards: int = 5,
    ) -> None:
        if total_shards != self.TOTAL_SHARDS:
            raise ValueError("This implementation requires exactly 5 total shards")
        if redundancy_threshold != self.DATA_SHARDS:
            raise ValueError("This implementation requires a 3-of-5 threshold")

        self.redundancy_threshold = redundancy_threshold
        self.total_shards = total_shards

    @staticmethod
    def _gf_mul(a: int, b: int) -> int:
        result = 0
        while b:
            if b & 1:
                result ^= a
            b >>= 1
            a <<= 1
            if a & 0x100:
                a ^= 0x11D
        return result & 0xFF

    @classmethod
    def _gf_pow(cls, value: int, exponent: int) -> int:
        result = 1
        while exponent:
            if exponent & 1:
                result = cls._gf_mul(result, value)
            value = cls._gf_mul(value, value)
            exponent >>= 1
        return result

    @classmethod
    def _gf_inv(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Zero has no multiplicative inverse")
        return cls._gf_pow(value, 254)

    @classmethod
    def _invert_matrix(cls, matrix: List[List[int]]) -> List[List[int]]:
        n = len(matrix)
        if n == 0 or any(len(row) != n for row in matrix):
            raise ValueError("Matrix must be non-empty and square")

        augmented = [
            row[:] + [1 if i == j else 0 for j in range(n)]
            for i, row in enumerate(matrix)
        ]

        for col in range(n):
            pivot = next(
                (row for row in range(col, n) if augmented[row][col] != 0),
                None,
            )
            if pivot is None:
                raise ValueError("Shard matrix is singular")

            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
            scale = cls._gf_inv(augmented[col][col])
            augmented[col] = [cls._gf_mul(value, scale) for value in augmented[col]]

            for row in range(n):
                if row == col:
                    continue
                factor = augmented[row][col]
                if factor:
                    augmented[row] = [
                        left ^ cls._gf_mul(factor, right)
                        for left, right in zip(augmented[row], augmented[col])
                    ]

        return [row[n:] for row in augmented]

    @classmethod
    def _generator_row(cls, index: int) -> List[int]:
        if not 0 <= index < cls.TOTAL_SHARDS:
            raise ValueError("Invalid shard index")

        if index < cls.DATA_SHARDS:
            return [1 if column == index else 0 for column in range(cls.DATA_SHARDS)]

        x = index - cls.DATA_SHARDS + 1
        return [cls._gf_pow(x, power) for power in range(cls.DATA_SHARDS)]

    @classmethod
    def _combine(cls, coefficients: Sequence[int], chunks: Sequence[bytes]) -> bytes:
        if not chunks:
            return b""
        size = len(chunks[0])
        if any(len(chunk) != size for chunk in chunks):
            raise ValueError("Shard sizes do not match")

        output = bytearray(size)
        for coefficient, chunk in zip(coefficients, chunks):
            if coefficient == 0:
                continue
            if coefficient == 1:
                for offset, byte in enumerate(chunk):
                    output[offset] ^= byte
            else:
                for offset, byte in enumerate(chunk):
                    output[offset] ^= cls._gf_mul(coefficient, byte)
        return bytes(output)

    @staticmethod
    def _hash_shard(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def shard_code(self, source_code: str) -> List[Dict[str, object]]:
        if not isinstance(source_code, str):
            raise TypeError("source_code must be a string")

        data = source_code.encode("utf-8")
        original_length = len(data)
        chunk_size = max(1, (original_length + self.DATA_SHARDS - 1) // self.DATA_SHARDS)
        padded = data.ljust(chunk_size * self.DATA_SHARDS, b"\x00")
        data_chunks = [
            padded[i * chunk_size : (i + 1) * chunk_size]
            for i in range(self.DATA_SHARDS)
        ]

        chunks = list(data_chunks)
        for index in range(self.DATA_SHARDS, self.TOTAL_SHARDS):
            chunks.append(self._combine(self._generator_row(index), data_chunks))

        result: List[Dict[str, object]] = []
        for index, chunk in enumerate(chunks):
            result.append(
                {
                    "index": index,
                    "payload": chunk.hex(),
                    "checksum": self._hash_shard(chunk),
                    "scheme": self.SCHEME,
                    "original_length": original_length,
                    "chunk_size": chunk_size,
                }
            )
        return result

    def place_on_chain(
        self, chain_state: List[Dict], source_code: str
    ) -> List[Dict[str, object]]:
        shards = self.shard_code(source_code)
        for shard in shards:
            chain_state.append(
                {
                    "type": "CODE_SHARD",
                    "shard_index": shard["index"],
                    "payload": shard["payload"],
                    "checksum": shard["checksum"],
                    "scheme": shard["scheme"],
                    "original_length": shard["original_length"],
                    "chunk_size": shard["chunk_size"],
                }
            )
        return shards

    def reconstruct(self, chain_state: List[Dict]) -> str:
        """Recover original UTF-8 source from any three valid shards."""
        by_index: Dict[int, bytes] = {}
        metadata = None

        for block in chain_state:
            if not isinstance(block, dict) or block.get("type") != "CODE_SHARD":
                continue

            try:
                index = block["shard_index"]
                payload_hex = block["payload"]
                checksum = block["checksum"]
                scheme = block["scheme"]
                original_length = block["original_length"]
                chunk_size = block["chunk_size"]

                if type(index) is not int or not 0 <= index < self.TOTAL_SHARDS:
                    continue
                if scheme != self.SCHEME:
                    continue
                if type(original_length) is not int or original_length < 0:
                    continue
                if type(chunk_size) is not int or chunk_size < 1:
                    continue
                if not isinstance(payload_hex, str) or len(payload_hex) % 2:
                    continue

                payload = bytes.fromhex(payload_hex)
                if len(payload) != chunk_size:
                    continue
                if self._hash_shard(payload) != checksum:
                    continue

                current_metadata = (original_length, chunk_size, scheme)
                if metadata is not None and current_metadata != metadata:
                    continue
                if index in by_index and by_index[index] != payload:
                    by_index.pop(index, None)
                    continue

                metadata = current_metadata
                by_index[index] = payload
            except (KeyError, TypeError, ValueError):
                continue

        if len(by_index) < self.DATA_SHARDS or metadata is None:
            raise RuntimeError(
                f"Insufficient valid shards: found {len(by_index)}, but {self.DATA_SHARDS} required"
            )

        original_length, chunk_size, _ = metadata
        selected = sorted(by_index.items())[: self.DATA_SHARDS]
        indices = [index for index, _ in selected]
        chunks = [chunk for _, chunk in selected]

        matrix = [self._generator_row(index) for index in indices]
        inverse = self._invert_matrix(matrix)
        data_chunks = [
            self._combine(inverse[row], chunks) for row in range(self.DATA_SHARDS)
        ]

        recovered = b"".join(data_chunks)
        if original_length > len(recovered):
            raise RuntimeError("Invalid original length metadata")
        recovered = recovered[:original_length]

        try:
            return recovered.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError("Recovered data is not valid UTF-8") from exc


class SelfHostRuntime:
    """Prototype runtime that persists and reconstructs its own source."""

    def __init__(self, source_code: str) -> None:
        self.source_code = source_code
        self.manager = ChainShardManager()
        self.chain_state: List[Dict] = []

    def persist_self(self) -> List[Dict]:
        self.manager.place_on_chain(self.chain_state, self.source_code)
        return self.chain_state

    def recover_self(self) -> str:
        return self.manager.reconstruct(self.chain_state)

    def validate_self(self) -> bool:
        try:
            recovered = self.recover_self()
        except Exception:
            return False
        return recovered == self.source_code


if __name__ == "__main__":
    source = """print('self-hosted prototype')\n"""
    runtime = SelfHostRuntime(source)
    runtime.persist_self()
    print(runtime.validate_self())
