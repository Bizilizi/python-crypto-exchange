import typing as t
from collections import defaultdict
from enum import Enum, auto

from exchange.libs.event_emitter import EventEmitter

from .entities.account import Account
from .entities.order import Order
from .entities.order_book import OrderBook
from .entities.symbol_pair import SymbolPair
from .errors import (
    IncorrectPrice,
    InsufficientFunds,
    OrderCancellationError,
    PairAlreadyExisted,
    PairDeletionError,
    UnsupportedPairs,
    WrongCredentials,
    WrongOrderID,
)
from .match_model import (
    MatchModel,
    MatchReport,
    MatchReportType,
    ReportOwnerType,
)


class ExchangeEvent(Enum):
    OrderBookUpdated = auto()
    OrderClosed = auto()
    OrderCreated = auto()
    OrderCancelled = auto()


class Exchange(EventEmitter[ExchangeEvent]):
    # singleton initialization
    def __new__(cls) -> "Exchange":
        if not hasattr(cls, "instance"):
            cls.instance: "Exchange" = super(Exchange, cls).__new__(cls)
        return cls.instance

    _accounts: t.Dict[str, Account]
    _created_orders: t.Dict[int, Order]
    _order_book: t.Dict[SymbolPair, OrderBook]

    _frozen_deposits: t.Dict[int, t.Tuple[str, float]]

    def __init__(self) -> None:
        super().__init__()
        self._accounts = {}
        self._created_orders = {}
        self._order_book = {}
        self._frozen_deposits = dict()

    # region pair management
    def get_order_book(self, pair: SymbolPair) -> OrderBook:
        try:
            return self._order_book[pair]
        except KeyError:
            raise UnsupportedPairs

    def clear_order_book(self, pair: SymbolPair) -> None:
        self._order_book[pair] = OrderBook([], [])

    def create_pair(self, pair: SymbolPair) -> None:
        if pair in self._order_book.keys():
            raise PairAlreadyExisted("Pair already exists")
        self._order_book[pair] = OrderBook([], [])

    def delete_pair(self, pair: SymbolPair) -> None:
        if pair not in self._order_book.keys():
            raise PairDeletionError("Pair was not found")
        self._order_book.pop(pair)

    @property
    def pairs(self) -> t.List[SymbolPair]:
        return list(self._order_book.keys())

    # endregion

    # region account management

    def refill_account(
        self, account_name: str, balance_map: t.Dict[str, float]
    ) -> None:
        if account_name not in self._accounts:
            raise WrongCredentials("Account with such credentials is not found")

        account = self._accounts[account_name]

        for key, value in balance_map.items():
            account.balance[key] += value

    def create_acc(self, account_name: str, balance_map: t.Dict[str, float]) -> Account:
        if account_name in self._accounts:
            raise WrongCredentials("Account already exists")
        account = Account(
            name=account_name, balance=defaultdict(float, **balance_map), open_orders={}
        )
        self._accounts[account_name] = account
        return account

    def delete_acc(self, account_name: str) -> None:
        if account_name not in self._accounts:
            raise WrongCredentials("Account with such credentials is not found")
        self._accounts.pop(account_name)

    def get_account(self, account_name: str) -> Account:
        try:
            return self._accounts[account_name]
        except KeyError:
            raise WrongCredentials("Account with such credentials is not found")

    @property
    def accounts(self) -> t.List[Account]:
        return list(self._accounts.values())

    # endregion

    # region order management
    def get_order(self, order_id: int) -> Order:
        try:
            return self._created_orders[order_id]
        except KeyError:
            raise WrongOrderID

    async def cancel_order(self, pair: SymbolPair, order_id: int) -> None:
        if order_id not in self._created_orders:
            raise WrongOrderID
        if pair not in self._order_book.keys():
            raise UnsupportedPairs

        order = self._created_orders[order_id]

        if order.order_type == Order.Type.Market:
            raise OrderCancellationError("Cannot close market order")

        await order.is_matched()  # wait for execution in case it's in process of matching

        if order.status == Order.Status.Closed:
            raise OrderCancellationError("Order already is closed")

        order_book = self._order_book[pair]
        if order in order_book:
            order.mark_closed()
            await self.emit(
                ExchangeEvent.OrderCancelled, order_id=order.order_id,
            )

            account = order.account

            # Delete order
            order_book.delete(order)
            del account.open_orders[order.order_id]

            # Return frozen assets
            symbol, frozen_funds = self._frozen_deposits[order.order_id]
            account.balance[symbol] += frozen_funds

            del self._frozen_deposits[order.order_id]

    async def create_limit(
        self,
        pair: SymbolPair,
        price: float,
        side: Order.Side,
        amount: float,
        acc_name: str,
    ) -> Order:
        if pair not in self._order_book.keys():
            raise UnsupportedPairs("Pair is not supported")

        order_book = self._order_book[pair]
        account = self.get_account(acc_name)
        price = round(price, order_book.min_price_power)

        if not price:
            raise IncorrectPrice("Pair is not supported")

        order = Order(
            symbol_pair=pair,
            amount=amount,
            price=price,
            side=side,
            account=account,
            order_type=Order.Type.Limit,
        )

        return await self._perform_match(order_book, order)

    async def create_market(
        self, pair: SymbolPair, side: Order.Side, amount: float, acc_name: str
    ) -> Order:
        if pair not in self._order_book:
            raise UnsupportedPairs("Pair is not supported")
        account = self.get_account(acc_name)
        order = Order(
            symbol_pair=pair,
            amount=amount,
            side=side,
            account=account,
            order_type=Order.Type.Market,
        )
        order_book = self._order_book[pair]

        return await self._perform_match(order_book, order)

    # endregion

    async def _match_preparation(self, order: Order) -> None:
        async with order.account:
            await self._froze_assets(order, order.account)

        self._created_orders[order.order_id] = order

        order.account.open_orders[order.order_id] = order
        await self.emit(
            ExchangeEvent.OrderCreated, order_id=order.order_id,
        )

    async def _perform_match(self, order_book: OrderBook, order: Order) -> Order:
        async with order_book:
            await self._match_preparation(order)

            if order.status != Order.Status.Closed:
                if order.order_type == Order.Type.Limit:
                    reports = await MatchModel.limit_match(
                        taker=order, order_book=order_book
                    )
                else:
                    reports = await MatchModel.market_match(
                        taker=order, order_book=order_book
                    )

                await self._process_reports(order_book, order, *reports)

        return order

    async def _process_reports(
        self, order_book: OrderBook, taker: Order, *reports: MatchReport
    ) -> None:
        def restore_difference(order: Order, actual_spent: float) -> None:
            # Restore taker difference in actual spent funds and frozen funds
            symbol, frozen_funds = self._frozen_deposits[order.order_id]

            if order.order_type == Order.Type.Limit:
                expected_to_spend = (
                    order.filled
                    if order.side == Order.Side.Sell
                    else order.filled * order.price  # type: ignore
                )

                self._frozen_deposits[order.order_id] = (
                    symbol,
                    frozen_funds - expected_to_spend,
                )
            else:
                expected_to_spend = frozen_funds

            order.account.balance[symbol] += expected_to_spend - actual_spent

        taker_real_spending = 0.0

        updated_prices: t.Set[t.Tuple[float, Order.Side]] = set()

        closed_ids = {
            report.order.order_id
            for report in reports
            if report.order.status == Order.Status.Closed
        }

        for report in reports:
            order = report.order
            account = order.account
            commission = 1 - (
                account.maker_fee
                if report.owner_type == ReportOwnerType.Maker
                else account.taker_fee
            )
            if order.price is not None:
                updated_prices.add((order.price, order.side))

            # Recalculate balance
            if order.side == Order.Side.Buy:
                account.balance[order.symbol_pair.Base] += (
                    report.base_matched * commission
                )

                # Restore maker difference in actual spent funds and frozen funds
                if report.owner_type == ReportOwnerType.Maker:
                    restore_difference(order, report.quote_matched)

                # Accumulate taker actual spent funds
                if report.owner_type == ReportOwnerType.Taker:
                    taker_real_spending += report.quote_matched
            else:
                account.balance[order.symbol_pair.Quote] += (
                    report.quote_matched * commission
                )

                # Restore maker difference in actual spent funds and frozen funds
                if report.owner_type == ReportOwnerType.Maker:
                    restore_difference(order, report.base_matched)

                # Accumulate taker actual spent funds
                if report.owner_type == ReportOwnerType.Taker:
                    taker_real_spending += report.base_matched

            # Delete order if it was matched
            if report.match_type == MatchReportType.Full:
                del account.open_orders[order.order_id]

        # Send Update Event:
        for price, side in updated_prices:
            await self.emit(
                ExchangeEvent.OrderBookUpdated,
                symbol_pair=taker.symbol_pair,
                side=taker.side,
                price=price,
            )

        # Restore taker difference in actual spent funds and frozen funds
        restore_difference(taker, taker_real_spending)

        for order_id in closed_ids:
            del self._frozen_deposits[order_id]
            await self.emit(
                ExchangeEvent.OrderClosed, order_id=order_id,
            )

    @staticmethod
    def _market_quote_size(order_book: OrderBook, order: Order) -> float:
        required = 0.0
        base_left = order.amount
        for maker in order_book.Asks:
            if base_left != 0:
                break
            amount = min(maker.amount, base_left)
            required += amount * maker.price  # type: ignore
            base_left -= amount

        return required

    async def _froze_assets(self, order: Order, account: Account) -> None:
        base_balance = account.balance[order.symbol_pair.Base]
        quote_balance = account.balance[order.symbol_pair.Quote]
        order_book = self.get_order_book(order.symbol_pair)

        # In case of Market buy order, we grant access for the order book and synchronously estimate required quote size
        # If order amount is more than ask size we will get accumulated ask quote size as required
        if order.order_type == Order.Type.Market and order.side == Order.Side.Buy:
            required = self._market_quote_size(order_book, order)
            if quote_balance >= required:
                account.balance[order.symbol_pair.Quote] -= required
                self._frozen_deposits[order.order_id] = (
                    order.symbol_pair.Quote,
                    required,
                )
            else:
                raise InsufficientFunds
        # In other cases we can froze assets without any problem
        elif order.side == Order.Side.Buy:
            if quote_balance >= order.amount * order.price:  # type: ignore
                account.balance[order.symbol_pair.Quote] -= order.amount * order.price  # type: ignore
                self._frozen_deposits[order.order_id] = (
                    order.symbol_pair.Quote,
                    order.amount * order.price,  # type: ignore
                )
            else:
                raise InsufficientFunds
        else:
            if base_balance >= order.amount:
                account.balance[order.symbol_pair.Base] -= order.amount
                self._frozen_deposits[order.order_id] = (
                    order.symbol_pair.Base,
                    order.amount,
                )
            else:
                raise InsufficientFunds
