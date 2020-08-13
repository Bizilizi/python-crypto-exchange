import asyncio
import typing as t

import pytest
from exchange.libs.flow import InMemoryFlow


async def produce_numbers(number: int, stream: InMemoryFlow[int]) -> None:
    for i in range(number):
        await stream.send(i)
        await asyncio.sleep(0.1)
    await stream.close()


@pytest.mark.asyncio
async def test_single_consumer() -> None:
    """
    Test maintaining delay is working for get method
    """

    async def read_numbers(stream: InMemoryFlow[int]) -> t.List[int]:
        result = []
        async for num in stream:
            result.append(num)

        return result

    flow = InMemoryFlow()
    number = 10
    consumer = asyncio.create_task(read_numbers(flow))
    await asyncio.create_task(produce_numbers(number, flow))

    assert list(range(number)) == await consumer


@pytest.mark.asyncio
async def test_multiple_consumer() -> None:
    """
    Test maintaining delay is working for get method
    """

    async def read_numbers(stream: InMemoryFlow[int]) -> t.List[int]:
        result = []
        async for num in stream:
            result.append(num)

        return result

    flow = InMemoryFlow()
    number = 10

    first_consumer = asyncio.create_task(read_numbers(flow))
    second_consumer = asyncio.create_task(read_numbers(flow))
    await asyncio.create_task(produce_numbers(number, flow))

    assert list(range(number)) == await first_consumer
    assert list(range(number)) == await second_consumer
