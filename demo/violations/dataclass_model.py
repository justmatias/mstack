import dataclasses
from dataclasses import dataclass


@dataclass
class User:
    name: str


@dataclasses.dataclass(frozen=True)
class Item:
    name: str
    quantity: int
