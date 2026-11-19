from fixtures.valid.infra import InMemoryOrderRepository


def build_repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()
