from __future__ import annotations
import abc
import asyncio
import inspect
import typing as t

from .flow import in_memory_flow


if t.TYPE_CHECKING:
    from .flow import Flow, Fork


class Comparable(t.Protocol):
    def __eq__(self, other: t.Any) -> bool:
        ...


EType = t.TypeVar("EType", bound=Comparable)
Event = t.Tuple[EType, t.Dict[str, t.Any]]


class Dispatcher(t.Generic[EType]):
    _event_fork: Fork[Event[EType]]
    _trigger: EType
    _is_async_callback: bool

    def __init__(
        self,
        event_stream: "Flow[Event[EType]]",
        trigger_event: EType,
        callback: t.Callable[..., t.Any],
    ) -> None:
        self._event_fork = event_stream.fork()
        self._callback = callback
        self._trigger = trigger_event
        self._is_async_callback = inspect.iscoroutinefunction(callback)

    @property
    async def events(self) -> t.AsyncGenerator[Event[EType], None]:
        async for event, kwargs in self._event_fork:
            if event == self._trigger:
                yield event, kwargs

    def dispatch_forever(self) -> asyncio.Task[t.Any]:
        async def handle() -> None:
            async for event, kwargs in self.events:
                if inspect.iscoroutinefunction(self._callback):
                    if self._is_async_callback:
                        await self._callback(**kwargs)
                    else:
                        self._callback(**kwargs)

        task = asyncio.create_task(handle())

        return task

    def stop(self) -> None:
        self._event_fork.stop()


class Subscriptable(t.Generic[EType]):
    @abc.abstractmethod
    async def events(self) -> t.AsyncGenerator[Event[EType], None]:
        yield  # type: ignore

    @abc.abstractmethod
    def subscribe(
        self, event: EType, handler: t.Callable[..., t.Any]
    ) -> Dispatcher[EType]:
        pass


class EventEmitter(Subscriptable[EType]):
    _event_stream: "Flow[Event[EType]]"

    def __init__(self) -> None:
        self._event_stream = in_memory_flow.InMemoryFlow[Event[EType]]()

    @property
    async def events(self) -> t.AsyncGenerator[Event[EType], None]:
        async for event, kwargs in self._event_stream:
            yield event, kwargs

    async def filter(self, trigger: EType) -> t.AsyncGenerator[Event[EType], None]:
        async for event, kwargs in self._event_stream:
            if event == trigger:
                yield event, kwargs

    def subscribe(
        self, event: EType, handler: t.Callable[..., t.Any]
    ) -> Dispatcher[EType]:
        return Dispatcher(self._event_stream, event, handler)

    async def emit(self, event: EType, **kwargs: t.Any) -> None:
        await self._event_stream.send((event, kwargs))
