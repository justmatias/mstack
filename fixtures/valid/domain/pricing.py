from fixtures.valid.domain.models import Order


def order_total(order: Order) -> float:
    return sum(item.unit_price * item.quantity for item in order.items)
