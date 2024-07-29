import asyncio
from datetime import date
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from eventiq import CloudEvent, Service
from eventiq.backends.stub import StubBroker


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture
def broker():
    return StubBroker()


@pytest.fixture
def service(broker):
    return Service(broker=broker, name="test_service")


@pytest.fixture(scope="session")
def handler():
    async def example_handler(message: CloudEvent) -> int:
        assert isinstance(message, CloudEvent)
        return 42

    return example_handler


@pytest.fixture
def mock_consumer(handler):
    mock = AsyncMock(spec=handler)
    mock.__annotations__ = handler.__annotations__
    return mock


@pytest_asyncio.fixture()
async def running_service(service: Service, mock_consumer):
    service.subscribe(topic="test_topic")(mock_consumer)

    async with service.context():
        yield service


@pytest.fixture()
def ce() -> CloudEvent:
    return CloudEvent.new(
        {"today": date.today().isoformat(), "arr": [1, "2", 3.0]},
        type="TestEvent",
        topic="test_topic",
    )
