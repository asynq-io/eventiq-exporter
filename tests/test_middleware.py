from eventiq import CloudEvent, Service

from eventiq_exporter import PrometheusMiddleware


def test_prometheus_middleware(service):
    service.add_middleware(PrometheusMiddleware)
    assert any(isinstance(m, PrometheusMiddleware) for m in service.middlewares)


async def test_consumer_called(running_service: Service, ce: CloudEvent, mock_consumer):
    await running_service.publish(ce)
    mock_consumer.assert_awaited_once_with(ce)
