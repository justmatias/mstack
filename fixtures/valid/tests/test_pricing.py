import pydantic
import pytest

from fixtures.valid.domain import Item, Order, order_total


def test_total_sums_price_times_quantity_when_order_has_items() -> None:
    order = Order(
        order_id="A-1",
        items=[
            Item(name="pen", unit_price=2.0, quantity=3),
            Item(name="pad", unit_price=5.0, quantity=1),
        ],
    )

    assert order_total(order) == pytest.approx(11.0)


def test_total_is_zero_when_order_is_empty() -> None:
    assert not order_total(Order(order_id="A-2", items=[]))


def test_item_rejects_a_negative_price() -> None:
    with pytest.raises(pydantic.ValidationError):
        Item(name="pen", unit_price=-1.0, quantity=1)
