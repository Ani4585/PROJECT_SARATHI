import asyncio
import pytest
from sarathi.cqrs import (
    DomainEvent,
    AggregateRoot,
    EventStore,
    CommandBus,
    QueryBus,
    ProjectionManager,
)

class AccountAggregate(AggregateRoot):
    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id)
        self.balance = 0.0

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.raise_event("MoneyDeposited", {"amount": amount})

    def apply(self, event: DomainEvent):
        if event.event_type == "MoneyDeposited":
            self.balance += event.data["amount"]

def test_aggregate_and_event_store():
    acc = AccountAggregate("acc_999")
    acc.deposit(100.0)
    acc.deposit(50.0)

    assert acc.balance == 150.0
    events = acc.commit_events()
    assert len(events) == 2

    store = EventStore()
    store.append_events("acc_999", events)
    stored = store.get_events("acc_999")
    assert len(stored) == 2
    assert stored[1].data["amount"] == 50.0

def test_command_bus_dispatch():
    async def _test():
        bus = CommandBus()

        class TransferCommand:
            def __init__(self, from_id, to_id, amount):
                self.from_id = from_id
                self.to_id = to_id
                self.amount = amount

        async def handle_transfer(cmd):
            return f"transferred_{cmd.amount}_from_{cmd.from_id}_to_{cmd.to_id}"

        bus.register(TransferCommand, handle_transfer)
        res = await bus.dispatch(TransferCommand("acc_1", "acc_2", 500))
        assert res == "transferred_500_from_acc_1_to_acc_2"

    asyncio.run(_test())

def test_projection_manager():
    pm = ProjectionManager()
    total_deposited = 0.0

    def update_view(event: DomainEvent):
        nonlocal total_deposited
        total_deposited += event.data["amount"]

    pm.register_projector("MoneyDeposited", update_view)
    pm.apply_event(DomainEvent(aggregate_id="a1", event_type="MoneyDeposited", data={"amount": 300.0}))

    assert total_deposited == 300.0
