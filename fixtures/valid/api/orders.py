import logging

from fixtures.valid.domain import Item, Order, order_total
from fixtures.valid.infra import InMemoryOrderRepository

logger = logging.getLogger(__name__)


def place_order(
    repository: InMemoryOrderRepository, order_id: str, items: list[Item]
) -> float:
    order = Order(order_id=order_id, items=items)
    repository.save(order)
    total = order_total(order)
    logger.info("Placed order %s with total %.2f", order_id, total)
    return total
