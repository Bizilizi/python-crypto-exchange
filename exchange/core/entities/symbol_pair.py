import typing as t


class SymbolPair(t.NamedTuple):
    Base: str
    Quote: str

    def __str__(self) -> str:
        return f"{self.Base}/{self.Quote}"
