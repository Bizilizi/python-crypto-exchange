from __future__ import annotations
import asyncio
import typing as t

from .flow import Flow, Fork


_T = t.TypeVar("_T")


class InMemoryFork(Fork[_T]):
    _queue: asyncio.Queue[_T]
    _max_size: int
    _active: bool

    def __init__(self, maxsize: int = 0) -> None:
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._max_size = maxsize
        self._active = True

    async def send(self, data: _T) -> None:
        if 0 < self._max_size < self._queue.qsize():
            await self._queue.get()
        await self._queue.put(data)

    def is_stopped(self) -> bool:
        return not self._active

    async def stop(self) -> None:
        self._active = False
        await self.send(None)  # type: ignore

    def __aiter__(self) -> t.AsyncIterator[_T]:
        return self

    async def __anext__(self) -> _T:
        value = await self._queue.get()
        if self._active:
            return value
        raise StopAsyncIteration


class InMemoryFlow(Flow[_T]):
    _forks: t.List[InMemoryFork[_T]]
    _max_size: int
    _closed: bool

    def __init__(self, maxsize: int = 0):
        self._forks = []
        self._max_size = maxsize
        self._closed = False

    def forks_number(self) -> int:
        return len(self._forks)

    def is_closed(self) -> bool:
        return self._closed

    def fork(self) -> InMemoryFork[_T]:
        fork = InMemoryFork[_T](self._max_size)
        self._forks.append(fork)
        return fork

    async def send(self, data: _T) -> None:
        for fork in self._forks:
            await fork.send(data)

    async def close(self) -> None:
        self._closed = True
        for fork in self._forks:
            await fork.stop()
        self._forks = []

    def __aiter__(self) -> t.AsyncIterator[_T]:
        return self.fork()
