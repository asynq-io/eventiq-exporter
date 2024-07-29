from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from eventiq.exceptions import Fail, Skip
from eventiq.middleware import Middleware

if TYPE_CHECKING:
    from eventiq import CloudEvent, Consumer, Service

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)

DEFAULT_BUCKETS = (
    5,
    10,
    25,
    50,
    75,
    100,
    250,
    500,
    750,
    1000,
    2500,
    5000,
    7500,
    10000,
    30000,
    60000,
    600000,
    900000,
    float("inf"),
)


class PrometheusMiddleware(Middleware):
    def __init__(
        self,
        run_server: bool = False,
        registry: CollectorRegistry = REGISTRY,
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
        server_host: str = "0.0.0.0",  # nosec
        server_port: int = 8888,
        prefix: str = "",
        **http_server_options: Any,
    ):
        self.run_server = run_server
        self.registry = registry
        self.buckets = buckets
        self.server_host = server_host
        self.server_port = server_port
        self.message_start_times: dict[int, int] = {}
        self.prefix = prefix
        self.http_server_options = http_server_options

        self.in_progress = Gauge(
            self.format("messages_in_progress"),
            "Total number of messages being processed.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_messages_published = Counter(
            self.format("messages_published_total"),
            "Total number of messages published",
            ["topic", "service"],
            registry=self.registry,
        )
        self.total_messages = Counter(
            self.format("messages_total"),
            "Total number of messages processed.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_skipped_messages = Counter(
            self.format("messages_skipped_total"),
            "Total number of messages skipped processing.",
            registry=self.registry,
        )
        self.total_retried_messages = Counter(
            self.format("message_error_total"),
            "Total number of errored messages.",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.total_failed_messages = Counter(
            self.format("message_failed_total"),
            "Total number of messages failed",
            ["topic", "service", "consumer"],
            registry=self.registry,
        )
        self.message_durations = Histogram(
            self.format("message_duration_ms"),
            "Time spend processing message",
            ["topic", "service", "consumer"],
            registry=self.registry,
            buckets=self.buckets,
        )

    @staticmethod
    def current_millis() -> int:
        return time.monotonic_ns() // 1000

    def format(self, value: str) -> str:
        if self.prefix:
            return f"{self.prefix}_{value}"
        return value

    async def before_process_message(
        self, *, service: Service, consumer: Consumer, message: CloudEvent
    ):
        labels = (consumer.topic, service.name, consumer.name)
        self.in_progress.labels(*labels).inc()
        self.message_start_times[id(message)] = self.current_millis()

    async def after_process_message(
        self,
        *,
        service: Service,
        consumer: Consumer,
        message: CloudEvent,
        result: Any | None = None,
        exc: Exception | None = None,
    ) -> None:
        labels = (service.name, consumer.name, message.topic)
        self.in_progress.labels(*labels).dec()
        self.total_messages.labels(*labels).inc()
        message_start_time = self.message_start_times.pop(
            id(message), self.current_millis()
        )
        message_duration = self.current_millis() - message_start_time
        self.message_durations.labels(*labels).observe(message_duration)

    async def after_retry_message(
        self,
        *,
        service: Service,
        consumer: Consumer,
        message: CloudEvent,
        exc: Exception,
    ) -> None:
        labels = (service.name, consumer.name, message.topic)
        self.total_retried_messages.labels(*labels).inc()

    async def after_skip_message(
        self, *, service: Service, consumer: Consumer, message: CloudEvent, exc: Skip
    ) -> None:
        labels = (consumer.topic, service.name, consumer.name)
        self.total_skipped_messages.labels(*labels).inc()

    async def after_fail_message(
        self, *, service: Service, consumer: Consumer, message: CloudEvent, exc: Fail
    ):
        labels = (service.name, consumer.name, message.topic)
        self.total_failed_messages.labels(*labels).inc()

    async def after_publish(self, *, service: Service, message: CloudEvent, **kwargs):
        labels = (service.name, message.topic)
        self.total_messages_published.labels(*labels).inc()

    async def after_broker_connect(self, *, service: Service):
        if self.run_server:
            start_http_server(
                self.server_port,
                self.server_host,
                registry=self.registry,
                **self.http_server_options,
            )
