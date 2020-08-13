import asyncio
import typing as t
from dataclasses import dataclass, field

import numpy as np
from exchange.libs.bisect import (
    bisect_left,
    bisect_right,
    insort,
    reverse_insort,
)

from .order import Order


class Level1(t.NamedTuple):
    Ask: t.Optional[Order]
    Bid: t.Optional[Order]


@dataclass
class OrderBook:
    Asks: t.List[Order]
    Bids: t.List[Order]

    min_price_power = 6
    min_amount_power = 8

    min_amount = 10 ** (-min_amount_power)
    min_price = 10 ** (-min_price_power)

    _lock: asyncio.Lock = asyncio.Lock()
    _amount_per_price: t.Dict[float, float] = field(default_factory=dict)

    def get_amount(self, price: float) -> float:
        return self._amount_per_price.get(price, 0.0)

    def add(self, order: Order) -> None:
        if order.side == Order.Side.Sell:
            insort(self.Asks, order, key=lambda el: el.price)
        else:
            reverse_insort(self.Bids, order, key=lambda el: el.price)
        self._increase_amount(order)

    def delete(self, order: Order) -> None:
        try:
            if order.side == Order.Side.Sell:
                self.Asks.remove(order)
                self._decrease_amount(order)
                return
            if order.side == Order.Side.Buy:
                self.Bids.remove(order)
                self._decrease_amount(order)
        except ValueError:
            pass

    def get_first(self, side: Order.Side) -> Order:
        if side == Order.Side.Sell:
            return self.Asks[0]
        else:
            return self.Bids[0]

    def pop_first(self, side: Order.Side) -> None:
        if side == Order.Side.Sell:
            order = self.Asks.pop(0)
        else:
            order = self.Bids.pop(0)

        self._decrease_amount(order)

    def _decrease_amount(self, order: Order) -> None:
        if order.price is None:
            return

        if order.price not in self._amount_per_price:
            self._amount_per_price[order.price] = order.amount
        else:
            self._amount_per_price[order.price] -= order.amount

        if np.isclose(
            self._amount_per_price[order.price], 0, rtol=self.min_amount / 10
        ):
            del self._amount_per_price[order.price]

    def _increase_amount(self, order: Order) -> None:
        if order.price is None:
            return

        if order.price not in self._amount_per_price:
            self._amount_per_price[order.price] = order.amount
        else:
            self._amount_per_price[order.price] += order.amount

    def _order_biserch(self, order: Order) -> bool:

        if order.side == Order.Side.Sell:
            orders = self.Asks
            reversed = False
        else:
            orders = self.Bids
            reversed = True

        left = bisect_left(orders, order, key=lambda el: el.price, reversed=reversed)
        right = bisect_right(orders, order, key=lambda el: el.price, reversed=reversed)

        if left != right:
            region = orders[left:right]
            try:
                region.index(order)
                return True
            except ValueError:
                return False

        return False

    def __len__(self) -> int:
        return len(self.Asks) + len(self.Bids)

    def __contains__(self, item: t.Union[Order, int]) -> bool:
        if isinstance(item, Order):
            return self._order_biserch(item)
        elif isinstance(item, int):
            asks_ids = [order.order_id for order in self.Asks]
            bids_ids = [order.order_id for order in self.Bids]
            return item in asks_ids or item in bids_ids

    async def __aenter__(self) -> "OrderBook":
        await self._lock.acquire()
        return self

    @t.no_type_check
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._lock.release()
