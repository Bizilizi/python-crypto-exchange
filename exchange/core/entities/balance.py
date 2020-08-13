import typing as t


class BalanceRecord(t.NamedTuple):
    Symbol: str
    Amount: float


class PairBalance(t.NamedTuple):
    Base: BalanceRecord
    Quote: BalanceRecord
