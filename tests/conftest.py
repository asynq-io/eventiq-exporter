import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from eventiq import CloudEvent, Service
from eventiq.backends.stub import StubBroker
from eventiq.consumer import Consumer, FnConsumer
from eventiq.utils import utc_now


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture()
def broker():
    return StubBroker()


@pytest.fixture()
def service(broker):
    return Service(broker=broker, name="test_service")


@pytest.fixture(scope="session")
def handler():
    async def example_handler(message: CloudEvent) -> int:
        assert isinstance(message, CloudEvent)
        return 42

    return example_handler


@pytest.fixture()
def mock_consumer():
    # this is workaround for inspect.getsignature() of AsyncMock
    # https://github.com/python/cpython/issues/96127
    mock = MagicMock(return_value=AsyncMock())
    mock.__annotations__ = {"message": CloudEvent, "return": None}
    mock.__name__ = "mock_consumer"
    return mock


@pytest_asyncio.fixture()
async def running_service(service: Service, mock_consumer):
    consumer: Consumer = FnConsumer(
        fn=mock_consumer, event_type=CloudEvent, topic="test_topic"
    )
    service.consumer_group.add_consumer(consumer)
    task = asyncio.create_task(service.run(enable_signal_handler=False))
    await asyncio.sleep(0)
    yield service
    with suppress(asyncio.CancelledError):
        task.cancel()
        await task


@pytest.fixture()
def ce() -> CloudEvent:
    return CloudEvent.new(
        {"today": utc_now().date(), "arr": [1, "2", 3.0]},
        type="TestEvent",
        topic="test_topic",
    )
