import asyncio
import operator
import typing as t
from enum import Enum, auto

import numpy as np

from .entities.order import Order
from .entities.order_book import OrderBook


class ReportOwnerType(Enum):
    Maker = auto()
    Taker = auto()


class MatchReportType(Enum):
    Full = auto()
    Partial = auto()


class MatchReport(t.NamedTuple):
    owner_type: ReportOwnerType
    match_type: MatchReportType
    order: Order
    quote_matched: float
    base_matched: float


class MatchModel:
    @classmethod
    async def limit_match(
        cls, taker: Order, order_book: OrderBook
    ) -> t.List[MatchReport]:
        taker.mark_matching()
        reports = []
        rtol = 10 ** (-OrderBook.min_amount_power)

        maker_orders = (
            order_book.Asks if taker.side == Order.Side.Buy else order_book.Bids
        )
        comparator = operator.ge if taker.side == Order.Side.Buy else operator.le
        if maker_orders:
            while not np.isclose(taker.filled, taker.amount, rtol):
                try:
                    maker = maker_orders[0]
                    if comparator(taker.price, maker.price):
                        maker_report, taker_report = cls._match_orders(
                            taker, maker, rtol
                        )
                        reports.append(maker_report)
                        reports.append(taker_report)

                        if maker_report.order.status == Order.Status.Closed:
                            order_book.pop_first(maker.side)
                    else:
                        cls._add_to_order_book(order_book, taker)
                        break
                except IndexError:
                    cls._add_to_order_book(order_book, taker)
                    break

                await asyncio.sleep(0)
        else:
            cls._add_to_order_book(order_book, taker)

        taker.finish_matching()

        return reports

    @classmethod
    async def market_match(
        cls, taker: Order, order_book: OrderBook
    ) -> t.List[MatchReport]:
        reports = []
        rtol = 10 ** (-OrderBook.min_amount_power)

        maker_orders = (
            order_book.Asks if taker.side == Order.Side.Buy else order_book.Bids
        )

        if maker_orders:
            while not np.isclose(taker.filled, taker.amount, rtol):
                try:
                    maker = maker_orders[0]
                    maker_report, taker_report = cls._match_orders(taker, maker, rtol)
                    reports.append(maker_report)
                    reports.append(taker_report)

                    if maker_report.order.status == Order.Status.Closed:
                        order_book.pop_first(maker.side)

                except IndexError:
                    break

                await asyncio.sleep(0)

        taker.mark_closed()

        return reports

    @classmethod
    def _add_to_order_book(cls, order_book: OrderBook, order: Order) -> None:
        order.mark_opened()
        order_book.add(order)

    @classmethod
    def _match_orders(
        cls, taker: Order, maker: Order, rtol: float
    ) -> t.Tuple[MatchReport, MatchReport]:

        maker_report_type = MatchReportType.Partial
        taker_report_type = MatchReportType.Partial

        maker_left = maker.amount - maker.filled
        taker_left = taker.amount - taker.filled
        if maker_left < taker_left:
            taker.filled += maker_left
            maker.filled += maker_left
            recalculation_amount = maker_left
        else:
            taker.filled += taker_left
            maker.filled += taker_left
            recalculation_amount = taker_left

        if np.isclose(taker.filled, taker.amount, rtol):
            taker.mark_closed()
            taker_report_type = MatchReportType.Full

        if np.isclose(maker.filled, maker.amount, rtol):
            maker.mark_closed()
            maker_report_type = MatchReportType.Full

        return (
            MatchReport(
                ReportOwnerType.Maker,
                maker_report_type,
                maker,
                recalculation_amount * maker.price,  # type: ignore
                recalculation_amount,
            ),
            MatchReport(
                ReportOwnerType.Taker,
                taker_report_type,
                taker,
                recalculation_amount * maker.price,  # type: ignore
                recalculation_amount,
            ),
        )
