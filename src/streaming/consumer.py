"""Kafka consumer — background task for streaming sales events into Postgres."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from src.db.queries import UPSERT_ACTUALS_BATCH

log = logging.getLogger(__name__)


async def consume_sales_events(
    db,
    bootstrap_servers: str,
    topic: str,
    group_id: str,
    shutdown_event: asyncio.Event,
    batch_size: int = 100,
    batch_timeout: float = 5.0,
):
    """Background coroutine: consume sales events from Kafka, write to actuals table.

    Uses batched upserts for throughput and manual commits for reliability.
    Runs until `shutdown_event` is set, then drains and stops gracefully.

    Args:
        db: Database instance (from src.db.session.get_db()).
        bootstrap_servers: Kafka broker addresses.
        topic: Kafka topic to consume.
        group_id: Consumer group ID.
        shutdown_event: asyncio.Event — set this to signal graceful shutdown.
        batch_size: Max records to buffer before flushing to DB.
        batch_timeout: Max seconds before flushing partial batch.
    """
    try:
        from aiokafka import AIOKafkaConsumer
    except ImportError:
        log.warning("aiokafka not installed. Kafka consumer disabled.")
        return

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
        auto_offset_reset="latest",
    )

    await consumer.start()
    log.info("Kafka consumer started: topic=%s, group=%s, servers=%s", topic, group_id, bootstrap_servers)

    batch: list = []
    last_flush = asyncio.get_event_loop().time()

    try:
        while not shutdown_event.is_set():
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
                batch.append(msg)

                now = asyncio.get_event_loop().time()
                if len(batch) >= batch_size or (now - last_flush) >= batch_timeout:
                    await _flush_batch(db, batch)
                    await consumer.commit()
                    batch.clear()
                    last_flush = now

            except asyncio.TimeoutError:
                # Flush partial batch on timeout
                if batch:
                    await _flush_batch(db, batch)
                    await consumer.commit()
                    batch.clear()

    finally:
        # Drain remaining
        if batch:
            await _flush_batch(db, batch)
            await consumer.commit()
        await consumer.stop()
        log.info("Kafka consumer stopped")


async def _flush_batch(db, batch: list) -> None:
    """Write a batch of Kafka messages to the actuals table."""
    records = []
    for msg in batch:
        val = msg.value
        records.append((
            val.get("product_id", 0),
            val.get("store_id", 1),
            val.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
            float(val.get("quantity_sold", 0)),
            float(val.get("revenue", 0)) if val.get("revenue") else None,
            bool(val.get("is_promotion", False)),
        ))

    if records:
        await db.executemany(UPSERT_ACTUALS_BATCH, records)
        log.debug("Flushed %d events to actuals", len(records))
