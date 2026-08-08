from typing import List, Dict, Any, Callable

class EdgeWorker:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.offline_queue: List[Dict[str, Any]] = []

    def queue_request(self, req: Dict[str, Any]):
        self.offline_queue.append(req)

    async def replay_queue(self, handler: Callable[[Dict[str, Any]], Any]) -> int:
        replayed = 0
        while self.offline_queue:
            req = self.offline_queue.pop(0)
            await handler(req)
            replayed += 1
        return replayed
