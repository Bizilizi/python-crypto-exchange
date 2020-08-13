import asyncio
import datetime
import typing as t
import uuid
from enum import Enum


if t.TYPE_CHECKING:
    from .symbol_pair import SymbolPair
    from .account import Account


class Order:
    class Status(Enum):
        Opened = "opened"
        Matching = "matching"
        Closed = "closed"

    class Side(Enum):
        Sell = "sell"
        Buy = "buy"

    class Type(Enum):
        Limit = "limit"
        Market = "market"

    order_id: int
    status: Status
    filled: float
    amount: float
    price: t.Optional[float]
    side: Side
    symbol_pair: "SymbolPair"
    account: "Account"
    creation_datetime: datetime.datetime
    order_type: Type

    _is_in_matching: asyncio.Future  # type: ignore

    def __init__(
        self,
        amount: float,
        side: Side,
        symbol_pair: "SymbolPair",
        account: "Account",
        order_type: Type,
        price: t.Optional[float] = None,
    ):
        self.order_id = uuid.uuid1().int
        self.status = Order.Status.Opened
        self.filled = 0
        self.amount = amount
        self.price = price
        self.side = side
        self.symbol_pair = symbol_pair
        self.account = account
        self.creation_datetime = datetime.datetime.now()
        self.order_type = order_type

        self._is_in_matching = asyncio.Future()

    def to_json(self) -> t.Dict[str, t.Union[str, float, int, None]]:
        return {
            "order_id": self.order_id,
            "symbol_pair": str(self.symbol_pair),
            "status": self.status.value,
            "amount": self.amount,
            "filled": self.filled,
            "price": self.price,
            "side": self.side.value,
            "type": self.order_type.value,
            "creation_datetime": str(self.creation_datetime),
        }

    def mark_matching(self) -> None:
        self.status = Order.Status.Matching

    def mark_closed(self) -> None:
        self.status = Order.Status.Closed

    def mark_opened(self) -> None:
        self.status = Order.Status.Opened

    def finish_matching(self) -> None:
        if not self._is_in_matching.done():
            self._is_in_matching.set_result(None)

    async def is_matched(self) -> None:
        if self.status == Order.Status.Matching:
            await self._is_in_matching
