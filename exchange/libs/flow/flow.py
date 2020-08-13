from __future__ import annotations
import typing as t


_T = t.TypeVar("_T")


@t.runtime_checkable
class Fork(t.Protocol[_T]):
    async def send(self, data: _T) -> None:
        ...

    def is_stopped(self) -> bool:
        ...

    async def stop(self) -> None:
        ...

    def __aiter__(self) -> t.AsyncIterator[_T]:
        ...

    async def __anext__(self) -> _T:
        ...


@t.runtime_checkable
class Flow(t.Protocol[_T]):
    async def send(self, data: _T) -> None:
        ...

    def forks_number(self) -> int:
        ...

    def is_closed(self) -> bool:
        ...

    async def close(self) -> None:
        ...

    def __aiter__(self) -> t.AsyncIterator[_T]:
        ...

    def fork(self) -> Fork[_T]:
        ...
