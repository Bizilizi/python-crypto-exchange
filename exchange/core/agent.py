import asyncio
import typing as t

from .entities import SymbolPair
from .entities.account import Account
from .entities.order import Order
from .errors import (
    AgentError,
    OrderCancellationError,
    OrderCreationError,
)
from .exchange import Exchange


class CreateMarketOrder(t.NamedTuple):
    pair: SymbolPair
    side: Order.Side
    amount: float
    acc_name: str
    order_id: int


class CreateLimitOrder(t.NamedTuple):
    pair: SymbolPair
    price: float
    side: Order.Side
    amount: float
    acc_name: str
    order_id: int


class CancelOrder(t.NamedTuple):
    pair: SymbolPair
    order_id: int


class Sleep(t.NamedTuple):
    time: int


class Agent:
    _account: Account
    _instruction_list: t.List[
        t.Union[Sleep, CreateMarketOrder, CreateLimitOrder, CancelOrder]
    ]
    _order_book: t.Dict[int, Order]
    _working_event: asyncio.Event
    _task: t.Any
    _order_dict: t.Dict[int, int]
    _exchange = Exchange()
    is_run: bool

    def __init__(
        self,
        instructions: t.List[
            t.Union[Sleep, CreateMarketOrder, CreateLimitOrder, CancelOrder]
        ],
        account: Account,
    ):
        self._account = account
        self._instruction_list = instructions
        self._working_event = asyncio.Event()
        self._order_dict = {}
        self.is_run = False

    async def _run(self) -> None:
        for instruction in self._instruction_list:
            await self._working_event.wait()
            if isinstance(instruction, CreateLimitOrder):
                if instruction.order_id in self._order_dict:
                    raise OrderCreationError("Order is already exist")
                order = await self._exchange.create_limit(
                    instruction.pair,
                    instruction.price,
                    instruction.side,
                    instruction.amount,
                    instruction.acc_name,
                )
                self._order_dict[instruction.order_id] = order.order_id

            elif isinstance(instruction, CreateMarketOrder):
                if instruction.order_id in self._order_dict:
                    raise OrderCreationError("Order is already exist")
                order = await self._exchange.create_market(
                    instruction.pair,
                    instruction.side,
                    instruction.amount,
                    instruction.acc_name,
                )
                self._order_dict[instruction.order_id] = order.order_id

            elif isinstance(instruction, CancelOrder):
                try:
                    order_id = self._order_dict[instruction.order_id]
                except KeyError:
                    raise OrderCancellationError
                await self._exchange.cancel_order(instruction.pair, order_id)

            elif isinstance(instruction, Sleep):
                await asyncio.sleep(instruction.time)
        self.is_run = False

    async def run(self) -> None:
        if self.is_run:
            raise AgentError("Agent is already running")
        task = asyncio.create_task(self._run())
        self._task = task
        self._working_event.set()
        self.is_run = True
        await task

    def pause(self) -> None:
        self._working_event.clear()

    def stop(self) -> None:
        if not self.is_run:
            raise AgentError("Agent is already closed")
        self.pause()
        self._task.cancel()
        self.is_run = False
