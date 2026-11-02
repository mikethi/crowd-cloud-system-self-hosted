# crowd-cloud-system-self-hosted

This repository evolves the original Crowd-Cloud System prototype into a self-hosting design: the system stores and reconstructs its own code from shard records in a chain-like state, while wallet and placement logic model distributed resource coordination.

## What this version adds

- Self-hosted source persistence: the runtime can split its own Python implementation into Reed-Solomon shards and place them into a simulated chain state.
- Recovery and reconstitution: the same code can recover a working source representation from those shards.
- Adaptive shard placement: placement planning is kept deterministic and minimal-change, while respecting peer capacities and failure domains.
- Wallet accounting: resource contributions remain tracked as distributed capacity for storage, CPU, and memory.

## Design intent

The code treats the ledger as a durable backing structure for executable state. In this prototype, the chain is not a full blockchain implementation; instead, it acts as a deterministic store for shard metadata and reconstructed source material.

## Run the demo

```bash
python main.py
```

The demo shards the current runtime source, records the shards in a simulated chain state, reconstructs the source from those shards, and validates that the recovered representation matches the original code.
