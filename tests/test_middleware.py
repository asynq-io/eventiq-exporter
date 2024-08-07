from eventiq import CloudEvent, Service
from eventiq.exceptions import Fail, Retry, Skip

from eventiq_exporter import PrometheusMiddleware


async def test_consumer_called(running_service: Service, ce: CloudEvent, mock_consumer):
    await running_service.publish(ce)
    mock_consumer.assert_awaited_once_with(ce)


async def test_prometheus_middleware(service, mock_consumer, ce):
    mock_consumer.name = "test_consumer"
    mock_consumer.topic = "test.topic"
    middleware = None
    service.add_middleware(PrometheusMiddleware, run_server=True, addr="127.0.0.1")
    assert any(isinstance(m, PrometheusMiddleware) for m in service.middlewares)
    for m in service.middlewares:
        if isinstance(m, PrometheusMiddleware):
            middleware = m
            break
    assert isinstance(middleware, PrometheusMiddleware)
    await middleware.before_broker_connect()
    await middleware.before_process_message(consumer=mock_consumer, message=ce)
    await middleware.after_process_message(
        consumer=mock_consumer, message=ce, result=42
    )
    await middleware.after_process_message(consumer=mock_consumer, message=ce, exc=None)
    await middleware.after_process_message(
        consumer=mock_consumer, message=ce, exc=Exception()
    )
    await middleware.after_retry_message(
        consumer=mock_consumer, message=ce, exc=Retry(delay=1)
    )
    await middleware.after_fail_message(
        consumer=mock_consumer, message=ce, exc=Fail("test reason")
    )
    await middleware.after_skip_message(
        consumer=mock_consumer, message=ce, exc=Skip("test reason")
    )
    await middleware.before_publish(message=ce)
    await middleware.after_publish(message=ce)
