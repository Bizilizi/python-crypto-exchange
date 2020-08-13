import asyncio
import typing as t


if t.TYPE_CHECKING:
    from node.engine.order import Order


class Account(t.NamedTuple):
    name: str
    balance: t.DefaultDict[str, float]
    open_orders: t.Dict[int, "Order"]

    maker_fee: float = 0.005
    taker_fee: float = 0.008

    lock: asyncio.Lock = asyncio.Lock()

    async def __aenter__(self) -> "Account":
        await self.lock.acquire()
        return self

    @t.no_type_check
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()
