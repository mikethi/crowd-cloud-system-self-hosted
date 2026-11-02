# Crowd-Cloud System Self-Hosted

This repository extends the original Crowd-Cloud System prototype into a self-hosting architecture. In this model, the runtime can persist parts of its own source code into a chain-like ledger, distribute them across multiple replicas, recover them when required, and validate that the recovered code matches the original implementation.

The project is intentionally exploratory and experimental. It is not a production-ready blockchain, distributed runtime, or secure execution environment. Instead, it is a design prototype for how a system might carry executable state, resource accounting, and resilience logic through a simulated distributed chain.

## Why this repository exists

The original Crowd-Cloud System idea centers on a decentralized compute environment where users contribute resources such as storage, CPU, and memory. This repository takes that concept one step further by treating the ledger itself as a durable, self-referential storage substrate for code.

In plain terms:

- the system records code as shards
- those shards are placed across peers or simulated storage domains
- the runtime can reconstruct code when enough valid copies are available
- the system validates integrity using checksums and deterministic structure
- the ledger acts as a persistence layer for executable state

This is a blueprint for a self-hosting runtime, not a fully hardened distributed operating system.

## Core idea

The repository combines three concepts:

1. Decentralized resource accounting
   - wallets track contributed resources
   - resources include storage, CPU, and memory
   - capacity is modeled as a distribution signal rather than a production-grade scheduler

2. Adaptive shard placement
   - code and data can be split into multiple copies
   - placement logic tries to avoid duplicate failure domains
   - system aims for minimal movement while achieving desired redundancy

3. Self-referential code persistence
   - source code is encoded into Reed-Solomon-style shards
   - shard records are inserted into simulated chain state
   - the code can later rebuild itself from valid shard fragments

Together, these ideas create a prototype of a self-hosting system that can survive partial loss by recovering the original executable representation from stored fragments.

## Architecture summary

The repository is organized around a few major concepts:

- `main.py`
  - demo and orchestration entrypoint
  - shows the runtime creating a self-hosted code-state narrative

- `core/chain_shards.py`
  - Reed-Solomon-inspired sharding logic
  - chunking, parity generation, shard validation, and reconstruction

- `core/adaptive_placement.py`
  - peer and placement planning model
  - preserves existing replicas while balancing loads
  - ensures failure domains are not duplicated when possible

- `models/wallet.py`
  - wallet accounting model for resource handoff and pricing
  - tracks contributed resources and derived PPM-style cost signals

## How self-hosting works in this prototype

The system follows a simple lifecycle:

1. Source code is selected
2. It is split into data and parity shards
3. Metadata is stored in a pseudo-chain structure
4. A placement planner chooses where these shards would live
5. Reconstruction attempts to recover the original source from the available copies
6. The runtime validates that the restored source matches the original

This is a conceptual implementation of a self-hosting machine: the runtime relies on its own stored state to recover or reconstruct itself.

## Example flow

```python
from core.chain_shards import ChainShardManager

source = "print('self-hosted prototype')\n"
manager = ChainShardManager()
state = []
manager.place_on_chain(state, source)
recovered = manager.reconstruct(state)
assert recovered == source
```

This demonstrates the core self-hosting loop:

- encode the source into shards
- store those shards in a ledger-like collection
- recover from the ledger
- verify correctness

## Potential use cases

This repository is intentionally broad in scope, and the following are realistic conceptual use cases for the patterns it explores.

### 1. Self-healing application runtimes

A system may need to recover its own critical code or configuration when a node is partially corrupted or restarted. Instead of relying solely on a central repository, the runtime could keep a resilient ledger of encoded source fragments and reconstruct itself from those fragments when necessary.

Use cases:

- device firmware recovery
- minimal edge runtimes
- resilient kiosks or field systems
- autonomous gateways with intermittent connectivity

### 2. Distributed code persistence

Code or application modules could be split into many pieces and distributed across multiple nodes. A ledger tracks which shards exist and where they live. Reassembly occurs only when enough valid shards are present.

Use cases:

- archive systems for critical scripts
- distributed software repositories
- resilient code mirrors across regions
- scientific workflow runtimes with reproducibility requirements

### 3. Disaster recovery for critical services

If a service loses a runtime image or some application files, it may be able to recover from the ledger instead of requiring a full redeploy.

Use cases:

- emergency restoration of local services
- backup of small autonomous control systems
- degraded-mode reconstitution after partial data loss

### 4. Multi-node shared storage prototypes

This repository includes capacity-aware placement logic. It is useful for modeling a system where chunks are stored across many peers while respecting limits and respecting domain separation.

Use cases:

- storage federation experiments
- distributed data retention prototypes
- small-scale proof-of-concept replication systems
- infrastructure planning simulations

### 5. Resource-sharing coordination experiments

The wallet model tracks allocation of HDD, CPU, and memory across peers. This is a simplified representation of a resource marketplace or cooperative computing environment.

Use cases:

- cooperative cloud simulations
- peer-to-peer capacity coordination
- resource scheduling experiments
- decentralized capacity accounting prototypes

### 6. Trustless or semi-trustless accounting models

The repo explores pricing logic and ledger-like tracking, which can be relevant for distributed accounting, usage metering, and simulation of systems in which costs are derived from usage and capacity.

Use cases:

- resource pricing experiments
- metering prototypes
- incentive simulation for compute-sharing networks
- accounting overlays for decentralized systems

### 7. Data archival and long-term preservation

Sharding is useful for preserving important source code, configuration, and operational logic without relying on a single copy.

Use cases:

- code archaeology and historical preservation
- independent backups of critical infrastructure scripts
- regulation-friendly archival systems
- long-term verification of software state

### 8. Resilient edge computing

An edge environment may have partial connectivity, limited storage, and variable compute availability. A self-hosting storage scheme could help recover critical systems from distributed fragments.

Use cases:

- edge gateways
- satellite-connected systems
- remote industrial controllers
- disconnected IoT deployments

### 9. Simulation and prototyping of distributed autonomy

This repository is especially valuable as a simulation environment for testing how a distributed system might store and recover itself without centralized control.

Use cases:

- educational distributed systems projects
- research prototypes
- architecture exploration during design
- experiments in autonomy and redundancy

### 10. Blockchain-adjacent concepts without a production chain

This repository is not a blockchain, but it does model ledger-backed state and replicated fragments. It can be useful for exploring architecture ideas adjacent to blockchain storage, such as determinism, redundancy, integrity validation, and peer placement.

Use cases:

- blockchain design experiments
- ledger-backed persistence concepts
- research in code as data
- decentralized state models

## Why the repo is useful even as a prototype

Even without full production guarantees, the repository illustrates a number of useful engineering ideas:

- deterministic validation of recovered state
- redundancy without central bottlenecks
- minimal-change placement policies
- resource-aware coordination
- self-recovery patterns for critical logic

This is valuable for people exploring how a system might survive partial failure and preserve executable knowledge in a distributed environment.

## Current limitations

This project is intentionally conceptual. It does not yet provide:

- authenticated peer identity
- secure consensus
- immutable chain validation
- production-grade networking
- real distributed execution
- hostile environment security hardening
- cryptographic verification beyond checksum-style integrity checks

The current design is best understood as a prototype for distributed persistence and self-hosting ideas, not as a full runtime platform.

## Running the demo

From the repository root:

```bash
python main.py
```

The demo performs the following sequence:

- constructs a source payload
- shreds it into code shards
- records the shards in simulated chain state
- reconstructs the source from the stored fragments
- validates the recovered value matches the original

## Development status

This repository is in active prototype and design exploration. It is intended as a conceptual platform for experimenting with:

- self-hosting runtime patterns
- decentralized resource coordination
- cryptographic sharding logic
- resilience-oriented system design

## Future directions

Possible extensions include:

- persistent JSON ledger state across runs
- peer registry and distributed placement simulation
- stronger integrity signatures
- versioned code states
- dynamic self-healing runtime checks
- DAG-like or block-based state progression
- configurable shard counts and redundancy rules

## Summary

Crowd-Cloud System Self-Hosted explores a future where the runtime itself can persist, reconstruct, and validate its own executable state using a distributed ledger model. It combines sharding, adaptive placement, and wallet-style resource accounting to simulate a resilient decentralized application environment.

This repository is not intended to be a complete operating system or blockchain platform. Instead, it presents a solid foundation for exploring the architecture of a self-hosting distributed runtime.
