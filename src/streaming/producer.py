"""Kafka producer — helper for publishing forecast events."""

from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)


class ForecastProducer:
    """Async Kafka producer for publishing forecast events.

    Usage:
        producer = ForecastProducer(bootstrap_servers="kafka:9092")
        await producer.start()
        await producer.publish_forecast("SKU-12345", {"predicted_demand": 200.5})
        await producer.stop()
    """

    def __init__(self, bootstrap_servers: str, topic: str = "forecasts.generated"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self._producer = None

    async def start(self) -> None:
        """Initialize and start the Kafka producer."""
        try:
            from aiokafka import AIOKafkaProducer
        except ImportError:
            log.warning("aiokafka not installed. Forecast producer disabled.")
            self._producer = None
            return

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            enable_idempotence=True,
            compression_type="snappy",
        )
        await self._producer.start()
        log.info("Kafka producer started: topic=%s", self.topic)

    async def stop(self) -> None:
        """Gracefully stop the producer."""
        if self._producer is not None:
            await self._producer.stop()
            log.info("Kafka producer stopped")

    async def publish_forecast(self, product_id: str, forecast_data: dict[str, Any]) -> None:
        """Publish a forecast event to Kafka.

        Args:
            product_id: The product identifier.
            forecast_data: Dict with forecast fields (predicted_demand, lower_bound, etc.).
        """
        if self._producer is None:
            return

        event = {
            "product_id": product_id,
            **forecast_data,
        }
        await self._producer.send_and_wait(self.topic, event)
        log.debug("Published forecast for %s to %s", product_id, self.topic)

    @property
    def is_ready(self) -> bool:
        return self._producer is not None
