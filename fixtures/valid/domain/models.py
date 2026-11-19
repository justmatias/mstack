from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=1)


class Order(BaseModel):
    order_id: str
    items: list[Item]
