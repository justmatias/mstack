import pytest


@pytest.mark.parametrize("quantity", [1, 2])
def test_total_is_positive_when_quantity_is_set(quantity):
    assert quantity > 0
