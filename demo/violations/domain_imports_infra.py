from example_app.infra import InMemoryOrderRepository


def build_repository() -> InMemoryOrderRepository:
    return InMemoryOrderRepository()
