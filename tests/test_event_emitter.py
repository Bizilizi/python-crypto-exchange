import asyncio
from enum import Enum, auto

import pytest
from exchange.libs.event_emitter import EventEmitter


class Events(Enum):
    Message = auto()
    Error = auto()


class Emitter(EventEmitter[Events]):
    pass


EVENTS = [
    (Events.Message, dict(id=5, msg="hello")),
    (Events.Message, dict(id=7, msg="stranger")),
    (Events.Message, dict(id=9, msg="bb")),
    (Events.Message, dict(id=1, msg="stranger")),
    (Events.Error, dict(msg="pipeline is broken")),
]


@pytest.mark.asyncio
async def test_event_receiving() -> None:
    received_messages = []

    async def emit(emitter: Emitter) -> None:
        for event, kwargs in EVENTS:
            await emitter.emit(event, **kwargs)

    async def receive(id: int, msg: str):
        received_messages.append(dict(id=id, msg=msg))

    emitter = Emitter()
    dispatcher = emitter.subscribe(Events.Message, receive)

    emit_task = asyncio.create_task(emit(emitter))
    dispatcher.dispatch_forever()

    messages = [msg for event, msg in EVENTS if event == Events.Message]
    await emit_task
    assert received_messages == messages
