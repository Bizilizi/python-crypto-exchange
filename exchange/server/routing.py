import typing as t
from collections import defaultdict

from aiohttp import web
from exchange.core.entities import SymbolPair
from exchange.core.entities.order import Order
from exchange.core.exchange import Exchange

from . import schema
from .helper import DDoS, error, success


routes = web.RouteTableDef()

exchange_instance = Exchange()


# region admin endpoints
@routes.post("/account/create")
async def create_account(request: web.Request) -> web.Response:
    json_data = schema.CreateAccountRequest.parse_obj(await request.json())
    exchange_instance.create_acc(
        json_data.account_name,
        defaultdict(btc=json_data.btc, eth=json_data.eth, usdt=json_data.usdt),
    )
    return web.Response(text=f"Account {json_data.account_name} was created")


@routes.post("/account/delete")
async def delete_account(request: web.Request) -> web.Response:
    json_data = schema.DeleteAccountRequest.parse_obj(await request.json())
    exchange_instance.delete_acc(json_data.account_name)
    return web.Response(text=f"Account {json_data.account_name} was deleted")


@routes.get("/account/get_all")
async def get_all_accounts(request: web.Request) -> web.Response:
    answer = {}
    for account in exchange_instance.accounts:
        answer[account.name] = [account.balance, account.open_orders]
    return success(answer)


@routes.post("/pair/create")
async def create_supported_pair(request: web.Request) -> web.Response:
    json_data = schema.CreateSupportedPair.parse_obj(await request.json())
    pair = json_data.symbol_pair.split("_")
    exchange_instance.create_pair(SymbolPair(pair[0], pair[1]))
    return web.Response(text=f"Pair {pair} was created")


@routes.post("/pair/delete")
async def delete_supported_pair(request: web.Request) -> web.Response:
    json_data = schema.DeleteSupportedPair.parse_obj(await request.json())
    pair = json_data.symbol_pair.split("_")
    exchange_instance.delete_pair(SymbolPair(pair[0], pair[1]))
    return web.Response(text=f"Pair {pair} was deleted")


@routes.get("/pair/get_all")
async def get_all_supported_pair(request: web.Request) -> web.Response:
    return success({"pairs": exchange_instance.pairs})


# endregion

# http endpoints
@routes.post("/order/create")
@DDoS(request_count=5, time_limit=1)
async def create_order(request: web.Request) -> web.Response:
    order_data = schema.CreateOrderRequest.parse_obj(await request.json())
    pair = SymbolPair(*order_data.symbol_pair.split("_"))
    acc_name = order_data.account_id
    if order_data.side == "buy":
        order_side = Order.Side.Buy
    elif order_data.side == "sell":
        order_side = Order.Side.Sell
    else:
        return error(415, f"Side expected ether sell or buy, got {order_data.side}")

    if order_data.type == "market":
        order = await exchange_instance.create_market(
            pair, order_side, order_data.amount, acc_name
        )
    elif order_data.type == "limit":
        order = await exchange_instance.create_limit(
            pair,
            t.cast(float, order_data.price),
            order_side,
            order_data.amount,
            acc_name,
        )
    else:
        return error(
            415, f"Order type expected ether limit or market, got {order_data.side}"
        )

    return success(order.to_json())


@routes.get("/order")
@DDoS(request_count=5, time_limit=1)
async def get_order_info(request: web.Request) -> web.Response:
    json_data = schema.OrderInfoRequest.parse_obj(await request.json())
    order_id = json_data.order_id
    order = exchange_instance.get_order(order_id)
    order_info = order.to_json()
    return success(order_info)


@routes.get("/depth")
@DDoS(request_count=5, time_limit=1)
async def get_order_book(request: web.Request) -> web.Response:
    json_data = schema.DepthInfoRequest.parse_obj(await request.json())
    pair = SymbolPair(*json_data.symbol_pair.split("_"))
    order_book = exchange_instance.get_order_book(pair)
    answer = {
        "symbol_pair": pair,
        "bids": [[info.price, info.amount] for info in order_book.Bids],
        "asks": [[info.price, info.amount] for info in order_book.Asks],
    }
    return success(answer)


@routes.get("/account/balance")
@DDoS(request_count=5, time_limit=1)
async def get_account_balance(request: web.Request) -> web.Response:
    json_data = schema.AccountBalanceRequest.parse_obj(await request.json())
    answer = {}
    symbols = json_data.symbols
    acc = exchange_instance.get_account(json_data.account_id)
    for symbol in symbols:
        answer[symbol] = acc.balance[f"{symbol}"]
    return success(answer)


@routes.post("/order/cancel")
@DDoS(request_count=5, time_limit=1)
async def cancel_order(request: web.Request) -> web.Response:
    json_data = schema.OrderCancelRequest.parse_obj(await request.json())
    pair = SymbolPair(*json_data.symbol_pair.split("_"))
    order_id = json_data.order_id
    await exchange_instance.cancel_order(pair, order_id)
    return success({"order_id": order_id})


# endregion
