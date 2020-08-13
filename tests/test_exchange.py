import itertools
import random
import typing as t
from collections import defaultdict

import numpy as np
import pytest
from exchange.core.entities import SymbolPair
from exchange.core.entities.account import Account
from exchange.core.entities.order import Order
from exchange.core.errors import (
    PairAlreadyExisted,
    PairDeletionError,
    WrongCredentials,
)
from exchange.core.exchange import Exchange


PAIRS = [
    SymbolPair("btc", "usdt"),
    SymbolPair("btc", "eth"),
    SymbolPair("eth", "usdt"),
    SymbolPair("iota", "usdt"),
    SymbolPair("bch", "usdt"),
]


def random_generated_limit_orders(
    pair: SymbolPair, account: Account, min_price: float = 0.1
):
    orders = []

    # asks
    for price in np.linspace(min_price * 30, min_price * 100, 50):
        amount = random.randint(1, 10)
        orders.append(
            Order(amount, Order.Side.Sell, pair, account, Order.Type.Limit, price)
        )
    # bids
    for price in np.linspace(min_price, min_price * 25, 50):
        amount = random.randint(1, 10)
        orders.append(
            Order(amount, Order.Side.Buy, pair, account, Order.Type.Limit, price)
        )

    return orders


async def generate_random_order_book(
    mock_exchange: Exchange, pair: SymbolPair, account_name: str
) -> t.List[Order]:
    account = mock_exchange.get_account(account_name)
    random_orders = random_generated_limit_orders(pair, account, min_price=0.5)
    created_orders = []

    ask_size = sum(order.amount for order in random_orders) * 3
    bid_size = sum(order.amount * order.price for order in random_orders) * 3

    mock_exchange.refill_account(
        account.name, {pair.Base: ask_size, pair.Quote: bid_size}
    )
    for order in random_orders:
        created_order = await mock_exchange.create_limit(
            order.symbol_pair, order.price, order.side, order.amount, account_name
        )
        created_orders.append(created_order)

    return created_orders


def refill_account(
    mock_exchange: Exchange, account_name: str, pair: SymbolPair, order_book
):
    ask_max = max(order.amount * order.price for order in order_book.Asks)
    bid_max = max(order.amount for order in order_book.Bids)

    mock_exchange.refill_account(
        account_name,
        {
            pair.Base: bid_max * len(order_book.Bids),
            pair.Quote: ask_max * len(order_book.Asks),
        },
    )


@pytest.fixture(scope="module")
def exchange():
    mock_exchange = Exchange()
    for pair in PAIRS:
        mock_exchange.create_pair(pair)

    return mock_exchange


@pytest.fixture(scope="module", autouse=True)
def init_accounts(exchange: Exchange):
    exchange.create_acc("Vladimir", dict(btc=10 ** 6, eth=10 ** 6, usdt=10 ** 6))
    exchange.create_acc("Ewriji", dict(btc=10 ** 15, eth=10 ** 15, usdt=10 ** 12))


def book_is_empty(pair: SymbolPair) -> bool:
    return len(exchange.get_order_book(pair)) == 0


@pytest.mark.asyncio
async def test_account_creation(exchange: Exchange):
    test_acc_1 = exchange.create_acc(
        "TestAccount_1", dict(btc=200.0, eth=10000, usdt=10 ** 10)
    )
    test_acc_2 = exchange.create_acc(
        "TestAccount_2", dict(btc=200.0, eth=10000, usdt=10 ** 10)
    )

    assert exchange.get_account("TestAccount_1") == test_acc_1
    assert exchange.get_account("TestAccount_2") == test_acc_2

    assert test_acc_1 in exchange.accounts
    assert test_acc_2 in exchange.accounts

    with pytest.raises(WrongCredentials):
        exchange.create_acc("TestAccount_1", defaultdict(float))


@pytest.mark.asyncio
async def test_account_deletion(exchange: Exchange):
    test_acc_3 = exchange.create_acc(
        "TestAccount_3", dict(btc=200.0, eth=10000, usdt=10 ** 10)
    )

    assert exchange.get_account("TestAccount_3") == test_acc_3
    assert test_acc_3 in exchange.accounts

    exchange.delete_acc("TestAccount_3")
    assert test_acc_3 not in exchange.accounts

    with pytest.raises(WrongCredentials):
        exchange.delete_acc("TestAccount_3")

    with pytest.raises(WrongCredentials):
        exchange.get_account("TestAccount_3")


@pytest.mark.asyncio
async def test_account_refill(exchange: Exchange):
    exchange.create_acc("TestAccount_3", dict(btc=200.0, eth=10000, usdt=10 ** 10))

    exchange.refill_account("TestAccount_3", defaultdict(float, btc=100, eth=20))
    test_acc_3 = exchange.get_account("TestAccount_3")

    assert test_acc_3.balance["btc"] == 300
    assert test_acc_3.balance["eth"] == 10020
    assert test_acc_3.balance["usdt"] == 10 ** 10


@pytest.mark.asyncio
async def test_pair_management(exchange: Exchange):
    exchange.create_pair(SymbolPair("test", "pair1"))
    exchange.create_pair(SymbolPair("test", "pair2"))

    assert SymbolPair("test", "pair1") in exchange.pairs
    assert SymbolPair("test", "pair2") in exchange.pairs

    assert len(exchange.get_order_book(SymbolPair("test", "pair1"))) == 0
    assert len(exchange.get_order_book(SymbolPair("test", "pair2"))) == 0

    with pytest.raises(PairAlreadyExisted):
        exchange.create_pair(SymbolPair("test", "pair1"))

    exchange.delete_pair(SymbolPair("test", "pair1"))

    assert SymbolPair("test", "pair1") not in exchange.pairs
    assert SymbolPair("test", "pair2") in exchange.pairs

    with pytest.raises(PairDeletionError):
        exchange.delete_pair(SymbolPair("test", "pair1"))


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_limit_order_creation(exchange: Exchange, pair: SymbolPair):
    ewriji = exchange.get_account("Ewriji")
    created_orders = await generate_random_order_book(exchange, pair, "Ewriji")

    order_book = exchange.get_order_book(pair)
    for order in created_orders:
        assert order in order_book
        assert order.status == Order.Status.Opened
        assert order.order_id in ewriji.open_orders

    exchange.clear_order_book(pair)


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_limit_order_deletion(exchange: Exchange, pair: SymbolPair):
    created_orders = await generate_random_order_book(exchange, pair, "Ewriji")

    order_book = exchange.get_order_book(pair)
    for order in created_orders:
        assert order in order_book

    for order in created_orders[:10]:
        await exchange.cancel_order(pair, order.order_id)

    order_book = exchange.get_order_book(pair)

    for order in created_orders[:10]:
        assert order not in order_book
        assert order.order_id not in order.account.open_orders

    for order in created_orders[10:]:
        assert order in order_book
        assert order.order_id in order.account.open_orders


@pytest.mark.asyncio
async def test_order_book_cleaning(exchange: Exchange):
    pair = SymbolPair("cleaning", "test")
    exchange.create_pair(pair)
    exchange.refill_account("Vladimir", dict(cleaning=10 * 10, test=10 * 10))
    for _ in range(2):
        await exchange.create_limit(pair, 0.001, Order.Side.Buy, 1, "Vladimir")
    order_book = exchange.get_order_book(pair)
    assert len(order_book) != 0

    exchange.clear_order_book(pair)

    order_book = exchange.get_order_book(pair)
    assert len(order_book) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_limit_matching(exchange: Exchange, pair: SymbolPair):
    exchange.clear_order_book(pair)
    await generate_random_order_book(exchange, pair, "Ewriji")

    order_book = exchange.get_order_book(pair)

    refill_account(exchange, "Vladimir", pair, order_book)
    taker_account = exchange.get_account("Vladimir")
    maker_account = exchange.get_account("Ewriji")

    # perform partial matching
    partial_matched_orders = order_book.Asks[:2]
    partial_amount = (
        partial_matched_orders[0].amount + partial_matched_orders[1].amount * 0.6
    )
    partial_price = partial_matched_orders[-1].price
    taker_order = await exchange.create_limit(
        pair, partial_price, Order.Side.Buy, partial_amount, "Vladimir"
    )

    # check results of partial matching
    order_book = exchange.get_order_book(pair)
    assert partial_matched_orders[0] not in order_book
    assert partial_matched_orders[0].order_id not in maker_account.open_orders
    assert partial_matched_orders[1] in order_book
    assert partial_matched_orders[1].order_id in maker_account.open_orders
    assert taker_order not in order_book
    assert taker_order.order_id not in taker_account.open_orders

    assert partial_matched_orders[0].status == Order.Status.Closed
    assert partial_matched_orders[1].status == Order.Status.Opened
    assert taker_order.status == Order.Status.Closed

    assert np.isclose(
        partial_matched_orders[0].amount, partial_matched_orders[0].filled
    )
    assert np.isclose(
        partial_matched_orders[1].filled, partial_matched_orders[1].amount * 0.6
    )
    assert np.isclose(taker_order.amount, taker_order.filled)

    # perform full matching
    amount = partial_matched_orders[1].amount - partial_matched_orders[1].filled
    price = partial_matched_orders[1].price + 0.5
    taker_order = await exchange.create_limit(
        pair, price, Order.Side.Buy, amount, "Vladimir"
    )

    # check results of full matching
    order_book = exchange.get_order_book(pair)
    assert partial_matched_orders[1] not in order_book
    assert partial_matched_orders[1].order_id not in maker_account.open_orders
    assert taker_order not in order_book

    assert partial_matched_orders[1].status == Order.Status.Closed
    assert taker_order.status == Order.Status.Closed

    assert np.isclose(
        partial_matched_orders[1].filled, partial_matched_orders[1].amount
    )
    assert np.isclose(taker_order.amount, taker_order.filled)


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_market_matching(exchange: Exchange, pair: SymbolPair):
    exchange.clear_order_book(pair)
    await generate_random_order_book(exchange, pair, "Ewriji")

    order_book = exchange.get_order_book(pair)

    refill_account(exchange, "Vladimir", pair, order_book)
    maker_account = exchange.get_account("Ewriji")

    # perform partial matching
    partial_matched_orders = order_book.Bids[:2]
    partial_amount = (
        partial_matched_orders[0].amount + partial_matched_orders[1].amount * 0.87
    )
    taker_order = await exchange.create_market(
        pair, Order.Side.Sell, partial_amount, "Vladimir"
    )

    # check results of partial matching
    order_book = exchange.get_order_book(pair)
    assert partial_matched_orders[0] not in order_book
    assert partial_matched_orders[0].order_id not in maker_account.open_orders
    assert partial_matched_orders[1] in order_book
    assert partial_matched_orders[1].order_id in maker_account.open_orders

    assert partial_matched_orders[0].status == Order.Status.Closed
    assert partial_matched_orders[1].status == Order.Status.Opened
    assert taker_order.status == Order.Status.Closed

    assert np.isclose(taker_order.amount, taker_order.filled)
    assert np.isclose(
        partial_matched_orders[0].amount, partial_matched_orders[0].filled
    )
    assert np.isclose(
        partial_matched_orders[1].filled, partial_matched_orders[1].amount * 0.87
    )

    # perform full matching
    amount = partial_matched_orders[1].amount - partial_matched_orders[1].filled
    taker_order = await exchange.create_market(
        pair, Order.Side.Sell, amount, "Vladimir"
    )

    # check results of full matching
    order_book = exchange.get_order_book(pair)
    assert partial_matched_orders[1] not in order_book
    assert partial_matched_orders[1].order_id not in maker_account.open_orders

    assert partial_matched_orders[1].status == Order.Status.Closed
    assert taker_order.status == Order.Status.Closed

    assert np.isclose(
        partial_matched_orders[1].filled, partial_matched_orders[1].amount
    )
    assert np.isclose(taker_order.amount, taker_order.filled)


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_market_matching_horizon_case(exchange: Exchange, pair: SymbolPair):
    exchange.clear_order_book(pair)
    await generate_random_order_book(exchange, pair, "Ewriji")
    order_book = exchange.get_order_book(pair)

    vladimir = exchange.get_account("Vladimir")
    refill_account(exchange, "Vladimir", pair, order_book)

    sell_amount = sum(order.amount for order in order_book.Bids)
    buy_amount = sum(order.amount for order in order_book.Asks)

    bid_quote = sum(order.amount * order.price for order in order_book.Bids)
    ask_quote = sum(order.amount * order.price for order in order_book.Asks)

    taker_fee = 1 - vladimir.taker_fee

    # math all orders in bid
    snapshot_vladimir_quote = vladimir.balance[pair.Quote]
    snapshot_vladimir_base = vladimir.balance[pair.Base]

    taker = await exchange.create_market(
        pair, Order.Side.Sell, sell_amount * 1.6, "Vladimir"
    )
    order_book = exchange.get_order_book(pair)

    assert taker.status == Order.Status.Closed
    assert len(order_book.Bids) == 0
    assert np.isclose(
        snapshot_vladimir_quote + bid_quote * taker_fee, vladimir.balance[pair.Quote]
    )
    assert np.isclose(snapshot_vladimir_base - sell_amount, vladimir.balance[pair.Base])

    # math all orders in ask

    snapshot_vladimir_quote = vladimir.balance[pair.Quote]
    snapshot_vladimir_base = vladimir.balance[pair.Base]

    taker = await exchange.create_market(
        pair, Order.Side.Buy, buy_amount * 1.6, "Vladimir"
    )
    order_book = exchange.get_order_book(pair)

    assert taker.status == Order.Status.Closed
    assert len(order_book.Bids) == 0

    assert np.isclose(snapshot_vladimir_quote - ask_quote, vladimir.balance[pair.Quote])
    assert np.isclose(
        snapshot_vladimir_base + buy_amount * taker_fee, vladimir.balance[pair.Base]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_mixed_matching(exchange: Exchange, pair: SymbolPair):
    exchange.clear_order_book(pair)
    await generate_random_order_book(exchange, pair, "Ewriji")

    order_book = exchange.get_order_book(pair)

    refill_account(exchange, "Vladimir", pair, order_book)

    exchange.refill_account("Vladimir", {pair.Base: 100000, pair.Quote: 1000})
    old_order_book_len = len(order_book)

    # perform partial matching by market orders
    bid_orders = order_book.Bids[:4]
    partial_bid_amount = (
        bid_orders[0].amount + bid_orders[1].amount + bid_orders[2].amount * 0.2
    )

    ask_orders = order_book.Asks[:5]
    partial_ask_amount = (
        ask_orders[0].amount
        + ask_orders[1].amount
        + ask_orders[2].amount
        + ask_orders[3].amount * 0.4
    )

    market_ask_order = await exchange.create_market(
        pair, Order.Side.Sell, partial_bid_amount, "Vladimir"
    )
    market_bid_order = await exchange.create_market(
        pair, Order.Side.Buy, partial_ask_amount, "Vladimir"
    )

    for order in itertools.chain(bid_orders[:2], ask_orders[:3]):
        assert order.status == Order.Status.Closed

    assert bid_orders[-2].status == Order.Status.Opened
    assert ask_orders[-2].status == Order.Status.Opened

    assert market_ask_order.status == Order.Status.Closed
    assert market_bid_order.status == Order.Status.Closed

    # perform full matching by limit orders

    ask_price = ask_orders[-1].price
    ask_amount = ask_orders[-1].amount + ask_orders[-2].amount * 0.6

    bid_price = bid_orders[-1].price
    bid_amount = bid_orders[-1].amount + bid_orders[-2].amount * 0.8

    limit_ask_order = await exchange.create_limit(
        pair, bid_price, Order.Side.Sell, bid_amount, "Vladimir"
    )
    limit_bid_order = await exchange.create_limit(
        pair, ask_price, Order.Side.Buy, ask_amount, "Vladimir"
    )

    for order in itertools.chain(bid_orders, ask_orders):
        assert order.status == Order.Status.Closed
        assert np.isclose(order.amount, order.filled)

    assert limit_ask_order.status == Order.Status.Closed
    assert limit_bid_order.status == Order.Status.Closed

    assert np.isclose(limit_bid_order.amount, limit_bid_order.filled)
    assert np.isclose(limit_ask_order.amount, limit_ask_order.filled)

    order_book = exchange.get_order_book(pair)

    assert old_order_book_len - len(order_book) == len(ask_orders) + len(bid_orders)


@pytest.mark.asyncio
@pytest.mark.parametrize("pair", PAIRS)
async def test_simple_balance_recalculation(exchange: Exchange, pair: SymbolPair):
    exchange.clear_order_book(pair)

    price = random.triangular(0.1, 1)
    amount = random.triangular(1, 10000)

    account_1 = exchange.create_acc(
        "account_1", defaultdict(float, **{pair.Base: 10000, pair.Quote: 10000})
    )
    snapshot_1_quote = account_1.balance[pair.Quote]
    snapshot_1_base = account_1.balance[pair.Base]

    account_2 = exchange.create_acc(
        "account_2", defaultdict(float, **{pair.Base: 10000, pair.Quote: 10000})
    )
    snapshot_2_quote = account_2.balance[pair.Quote]
    snapshot_2_base = account_2.balance[pair.Base]

    maker_fee = 1 - account_1.maker_fee
    taker_fee = 1 - account_2.taker_fee

    await exchange.create_limit(pair, price, Order.Side.Buy, amount, "account_1")
    await exchange.create_limit(pair, price, Order.Side.Sell, amount, "account_2")

    assert np.isclose(snapshot_1_quote - amount * price, account_1.balance[pair.Quote])
    assert np.isclose(
        snapshot_1_base + amount * maker_fee, account_1.balance[pair.Base]
    )

    assert np.isclose(
        snapshot_2_quote + amount * price * taker_fee, account_2.balance[pair.Quote]
    )
    assert np.isclose(snapshot_2_base - amount, account_2.balance[pair.Base])

    exchange.delete_acc("account_1")
    exchange.delete_acc("account_2")


@pytest.mark.asyncio
async def test_partial_with_close_balance_recalculation(exchange: Exchange):
    pair = SymbolPair("partial_with_close", "balance_recalculation")
    exchange.create_pair(pair)

    amount = random.triangular(1, 10)

    exchange.refill_account("Ewriji", {pair.Base: amount * 4, pair.Quote: amount * 4})
    exchange.refill_account("Vladimir", {pair.Base: amount * 4, pair.Quote: amount * 4})
    ewriji = exchange.get_account("Ewriji")
    vladimir = exchange.get_account("Vladimir")

    snapshot_ewriji_quote = ewriji.balance[pair.Quote]
    snapshot_ewriji_base = ewriji.balance[pair.Base]

    snapshot_vladimir_quote = vladimir.balance[pair.Quote]
    snapshot_vladimir_base = vladimir.balance[pair.Base]

    await exchange.create_limit(pair, 0.1, Order.Side.Sell, amount, "Ewriji")
    await exchange.create_limit(pair, 0.2, Order.Side.Sell, amount, "Ewriji")
    to_close = await exchange.create_limit(
        pair, 0.3, Order.Side.Sell, amount * 1.8, "Ewriji"
    )

    await exchange.create_limit(pair, 0.3, Order.Side.Buy, amount * 3, "Vladimir")

    maker_fee = 1 - ewriji.maker_fee
    taker_fee = 1 - vladimir.taker_fee

    ewriji_quote_shift = (amount * 0.1 + amount * 0.2 + amount * 0.3) * maker_fee

    assert np.isclose(
        snapshot_ewriji_quote + ewriji_quote_shift, ewriji.balance[pair.Quote]
    )
    assert np.isclose(snapshot_ewriji_base - amount * 3.8, ewriji.balance[pair.Base])

    assert np.isclose(
        snapshot_vladimir_quote - amount * 3 * 0.2, vladimir.balance[pair.Quote]
    )
    assert np.isclose(
        snapshot_vladimir_base + amount * 3 * taker_fee, vladimir.balance[pair.Base]
    )

    await exchange.cancel_order(pair, to_close.order_id)

    assert np.isclose(snapshot_ewriji_base - amount * 3, ewriji.balance[pair.Base])
