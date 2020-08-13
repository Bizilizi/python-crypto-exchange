import asyncio
import typing as t
from collections import defaultdict

import pytest
from exchange.core.agent import (
    Agent,
    CancelOrder,
    CreateLimitOrder,
    CreateMarketOrder,
    Sleep,
)
from exchange.core.entities import SymbolPair
from exchange.core.entities.account import Account
from exchange.core.entities.order import Order
from exchange.core.errors import (
    AgentError,
    OrderCreationError,
)
from exchange.core.exchange import Exchange


create_order_instructions = [
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=2,
        side=Order.Side.Buy,
        amount=2,
        acc_name="Vladimir",
        order_id=1,
    ),
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=3,
        side=Order.Side.Buy,
        amount=3,
        acc_name="Vladimir",
        order_id=2,
    ),
]

existed_order_instructions = [
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=1,
        side=Order.Side.Buy,
        amount=1,
        acc_name="Vladimir",
        order_id=1,
    ),
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=3,
        side=Order.Side.Buy,
        amount=3,
        acc_name="Vladimir",
        order_id=1,
    ),
]

cancel_order_instructions = [
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=1,
        side=Order.Side.Buy,
        amount=1,
        acc_name="Vladimir",
        order_id=1,
    ),
    CancelOrder(pair=SymbolPair("btc", "usdt"), order_id=1),
]

check_agent_runable_instructions = [
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=1,
        side=Order.Side.Buy,
        amount=1,
        acc_name="Vladimir",
        order_id=4,
    ),
    CreateLimitOrder(
        pair=SymbolPair("btc", "usdt"),
        price=3,
        side=Order.Side.Buy,
        amount=3,
        acc_name="Vladimir",
        order_id=5,
    ),
]


def mock_agent(
    instructions: t.List[
        t.Union[Sleep, CreateMarketOrder, CreateLimitOrder, CancelOrder]
    ]
):
    return Agent(
        instructions,
        account=Account(
            name="Vladimir",
            balance=defaultdict(btc=100, usdt=200, eth=300),
            open_orders={},
        ),
    )


@pytest.fixture
def exchange():
    mock_exchange = Exchange()
    mock_exchange.create_pair(SymbolPair("btc", "usdt"))
    mock_exchange.create_acc(
        account_name="Vladimir", balance_map=defaultdict(btc=100, usdt=200, eth=300)
    )
    return mock_exchange


@pytest.mark.asyncio
async def test_orders_creation(exchange: Exchange):
    agent = mock_agent(create_order_instructions)
    await agent.run()
    order_book = exchange.get_order_book(SymbolPair("btc", "usdt"))

    first_bid = order_book.Bids[0]
    first_instruction = create_order_instructions[1]

    second_bid = order_book.Bids[1]
    second_instruction = create_order_instructions[0]

    assert first_bid.price == first_instruction.price
    assert first_bid.amount == first_instruction.amount
    assert first_bid.symbol_pair == first_instruction.pair

    assert second_bid.price == second_instruction.price
    assert second_bid.amount == second_instruction.amount
    assert second_bid.symbol_pair == second_instruction.pair

    assert not agent.is_run


@pytest.mark.asyncio
async def test_order_cancel(exchange: Exchange):
    agent = mock_agent(cancel_order_instructions)
    await agent.run()
    assert len(exchange.get_order_book(SymbolPair("btc", "usdt"))) == 0
    assert not agent.is_run


@pytest.mark.asyncio
async def test_order_id_check(exchange: Exchange):
    with pytest.raises(OrderCreationError):
        agent = mock_agent(existed_order_instructions)
        await agent.run()


@pytest.mark.asyncio
async def test_agent_runable(exchange: Exchange):
    with pytest.raises(AgentError):
        agent = mock_agent(check_agent_runable_instructions)
        await asyncio.gather(agent.run(), agent.run())
