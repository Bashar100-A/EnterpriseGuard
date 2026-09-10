# Component: sibb_distributed.py

**Path:** `tools/sibb_distributed.py`
**Version:** 1.2
**Purpose:** Distributed WORM storage across 3+ nodes with quorum.
**Status:** Working (23/23 tests passed)

---

## What It Does

Wraps multiple WORMStorage instances (nodes) into a single
distributed storage layer with quorum-based writes and reads.

Tolerates up to N - quorum node failures.
Verifies integrity across all nodes.

## Architecture

- MIN_NODES = 3
- Default quorum = 2
- Each node is a full WORMStorage instance
- Writes go to all nodes; success if >= quorum succeed
- Reads from first healthy node with valid hash

## Inputs

- data (bytes)
- filename (string)
- optional metadata (dict)

## Outputs

- Per-node storage in configured base paths
- Each node has its own .worm_metadata.json

## Key Functions

| Function | Purpose |
|----------|---------|
| create_distributed_storage() | Create N-node cluster |
| StorageNode.write() | Write to one node |
| StorageNode.read() | Read from one node |
| StorageNode.verify() | Verify one node |
| DistributedStorage.write() | Write to all nodes (quorum) |
| DistributedStorage.read() | Read from first healthy node |
| DistributedStorage.verify() | Verify across all nodes |
| DistributedStorage.get_status() | Return cluster status |
| DistributedStorage.list_files() | List files from first healthy node |

## Node Status Values

| Status | Meaning |
|--------|---------|
| online | Node responds normally |
| degraded | Last operation failed (may recover) |
| corrupted | Hash mismatch detected |

## Quorum Rules

- write() succeeds if >= quorum nodes accept
- If any node fails with WORMStorageError (security), all nodes are rolled back
- read() iterates nodes, returns first valid response
- verify() checks each node independently

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| 1 node down (quorum=2, 3 nodes) | Write succeeds; node marked degraded |
| 2 nodes down (quorum=2) | Write fails with DistributedStorageError |
| Corrupted node | Marked corrupted, skipped on read |
| All nodes down | Read raises DistributedStorageError |

## Tests

- tests/test_sibb_distributed.py (23 tests, passing)

## Used By

- sibb_cli.py
- sibb_innocence_integration.py (distributed ring storage)

**End of Component Doc**
