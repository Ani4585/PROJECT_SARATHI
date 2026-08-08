import asyncio
import sarathi
import pytest
from sarathi.edge import VectorClock, SyncDelta, DistributedStateSync, EdgeWorker

def test_edge_version():
    assert sarathi.__version__ >= "1.6.0"

def test_vector_clock_and_state_sync():
    node1 = DistributedStateSync("node1")
    node2 = DistributedStateSync("node2")

    node1.set("theme", "dark")
    ts1 = node1.timestamps["theme"]

    node2.sync_delta("theme", "dark", ts1, node1.clock)
    assert node2.state["theme"] == "dark"

def test_edge_worker_offline_replay():
    async def _test():
        worker = EdgeWorker("edge_node_1")
        worker.queue_request({"action": "update_status", "status": "active"})

        processed = []
        async def mock_handler(req):
            processed.append(req["status"])

        replayed = await worker.replay_queue(mock_handler)
        assert replayed == 1
        assert processed == ["active"]

    asyncio.run(_test())
