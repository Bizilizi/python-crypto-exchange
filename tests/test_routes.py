import asyncio
from collections import defaultdict

import aiohttp
from aiohttp import web
from aiohttp.test_utils import (
    AioHTTPTestCase,
    unittest_run_loop,
)
from exchange.core.entities import SymbolPair
from exchange.core.exchange import Exchange
from exchange.server.app import application_factory


class APITestCase(AioHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_manager = Exchange()
        cls.model_manager.create_pair(SymbolPair("btc", "usdt"))
        cls.model_manager.create_pair(SymbolPair("btc", "eth"))
        cls.model_manager.create_pair(SymbolPair("eth", "usdt"))
        cls.model_manager.create_pair(SymbolPair("bpm", "spb"))
        cls.model_manager.create_acc("Vladimir", defaultdict(btc=10, eth=20, usdt=150))
        cls.model_manager.create_acc("Ewriji", defaultdict(btc=20, eth=30, usdt=200))

    async def get_application(self) -> web.Application:
        return await application_factory()

    @property
    def server_address(self) -> str:
        return f"http://{self.server.host}:{self.server.port}"

    @unittest_run_loop
    async def test_create_order(self):
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.server_address}/order/create",
                json={
                    "account_id": "Vladimir",
                    "type": "limit",
                    "amount": 1,
                    "price": 2,
                    "side": "buy",
                    "symbol_pair": "btc_usdt",
                },
            )
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            pair = data["result"]["symbol_pair"].split("/")
            assert (
                not len(self.model_manager.get_order_book(SymbolPair(pair[0], pair[1])))
                == 0
            )

    @unittest_run_loop
    async def test_get_order_info(self):
        async with aiohttp.ClientSession() as session:
            create_order = await session.post(
                f"{self.server_address}/order/create",
                json={
                    "account_id": "Ewriji",
                    "type": "limit",
                    "amount": 1,
                    "price": 2,
                    "side": "buy",
                    "symbol_pair": "btc_usdt",
                },
            )
            assert create_order.status == 200
            order_creation_data = await create_order.json()
            response = await session.get(
                f"{self.server_address}/order",
                json={
                    "account_id": "Ewriji",
                    "order_id": order_creation_data["result"]["order_id"],
                    "symbol_pair": "btc_usdt",
                },
            )
            assert response.status == 200
            order_info = await response.json()
            assert order_info["success"] is True
            assert (
                order_info["result"]["amount"]
                == order_creation_data["result"]["amount"]
            )
            assert (
                order_info["result"]["price"] == order_creation_data["result"]["price"]
            )
            assert order_info["result"]["side"] == order_creation_data["result"]["side"]

    @unittest_run_loop
    async def test_get_order_book(self):
        async with aiohttp.ClientSession() as session:
            create_order = await session.post(
                f"{self.server_address}/order/create",
                json={
                    "account_id": "Vladimir",
                    "type": "limit",
                    "amount": 1,
                    "price": 2,
                    "side": "buy",
                    "symbol_pair": "btc_usdt",
                },
            )
            assert create_order.status == 200
            order_creation_data = await create_order.json()
            response = await session.get(
                f"{self.server_address}/depth",
                json={"account_id": "Vladimir", "symbol_pair": "btc_usdt"},
            )
            assert response.status == 200
            data = await response.json()
            pair = data["result"]["symbol_pair"]
            assert (
                f"{pair[0]}/{pair[1]}" == order_creation_data["result"]["symbol_pair"]
            )
            assert data["success"] is True

    @unittest_run_loop
    async def test_get_account_balance(self):
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f"{self.server_address}/account/balance",
                json={"account_id": "Vladimir", "symbols": ["usdt", "btc", "eth"]},
            )
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert data["result"] is not None

    @unittest_run_loop
    async def test_cancel_order(self):
        async with aiohttp.ClientSession() as session:
            create_order = await session.post(
                f"{self.server_address}/order/create",
                json={
                    "account_id": "Ewriji",
                    "type": "limit",
                    "amount": 1,
                    "price": 2,
                    "side": "buy",
                    "symbol_pair": "btc_usdt",
                },
            )
            assert create_order.status == 200
            order_creation_data = await create_order.json()
            pair = order_creation_data["result"]["symbol_pair"].split("/")
            assert (
                not len(self.model_manager.get_order_book(SymbolPair(pair[0], pair[1])))
                == 0
            )
            response = await session.post(
                f"{self.server_address}/order/cancel",
                json={
                    "account_id": "Ewriji",
                    "symbol_pair": "btc_usdt",
                    "order_id": order_creation_data["result"]["order_id"],
                },
            )
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert (
                len(self.model_manager.get_order_book(SymbolPair(pair[0], pair[1])))
                == 0
            )

    @unittest_run_loop
    async def test_create_account(self):
        async with aiohttp.ClientSession() as session:
            create_account = await session.post(
                f"{self.server_address}/account/create",
                json={"account_name": "Kolya", "btc": 10, "eth": 15, "usdt": 200},
            )
            assert create_account.status == 200
            assert "Kolya" in [account.name for account in self.model_manager.accounts]

    @unittest_run_loop
    async def test_delete_account(self):
        async with aiohttp.ClientSession() as session:
            delete_account = await session.post(
                f"{self.server_address}/account/delete", json={"account_name": "Kolya"}
            )
            assert delete_account.status == 200
            assert "Kolya" not in [
                account.name for account in self.model_manager.accounts
            ]

    @unittest_run_loop
    async def test_create_pair(self):
        async with aiohttp.ClientSession() as session:
            create_pair = await session.post(
                f"{self.server_address}/pair/create", json={"symbol_pair": "bmx_gpt"}
            )
            assert create_pair.status == 200
            assert (
                self.model_manager.get_order_book(SymbolPair("bmx", "gpt")) is not None
            )

    @unittest_run_loop
    async def test_delete_pair(self):
        async with aiohttp.ClientSession() as session:
            delete_pair = await session.post(
                f"{self.server_address}/pair/delete", json={"symbol_pair": "bpm_spb"}
            )
            assert delete_pair.status == 200
            assert SymbolPair("bpm", "spb") not in self.model_manager.pairs

    @unittest_run_loop
    async def test_get_all_pairs(self):
        async with aiohttp.ClientSession() as session:
            get_all_pairs = await session.get(f"{self.server_address}/pair/get_all")
            assert get_all_pairs.status == 200
            data = await get_all_pairs.json()
            for pair in data["result"]["pairs"]:
                assert SymbolPair(pair[0], pair[1]) in self.model_manager.pairs

    @unittest_run_loop
    async def test_ddos(self):
        async with aiohttp.ClientSession() as session:
            for i in range(5):
                response = await session.post(
                    f"{self.server_address}/order/create",
                    json={
                        "account_id": "Vladimir",
                        "type": "limit",
                        "amount": 1,
                        "price": 2,
                        "side": "buy",
                        "symbol_pair": "btc_usdt",
                    },
                )
            data = await response.json()
            assert data["success"] is False
            assert data["message"] == "DDoS protection error. Too Many Requests"
            await asyncio.sleep(1)
