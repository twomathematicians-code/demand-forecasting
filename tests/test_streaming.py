"""Tests for streaming module (mock-based — no Kafka required)."""



class TestStreamingImports:
    """Verify streaming modules import correctly."""

    def test_consumer_import(self):
        from src.streaming.consumer import consume_sales_events
        assert callable(consume_sales_events)

    def test_producer_import(self):
        from src.streaming.producer import ForecastProducer
        producer = ForecastProducer("localhost:9092")
        assert producer.bootstrap_servers == "localhost:9092"
        assert not producer.is_ready

    def test_producer_lifecycle(self):
        from src.streaming.producer import ForecastProducer
        producer = ForecastProducer("localhost:9092", "test.topic")
        assert producer.topic == "test.topic"


class TestConsumerSignature:
    """Verify consumer function signature is correct."""

    def test_consumer_is_async_function(self):
        import inspect

        from src.streaming.consumer import consume_sales_events
        assert inspect.iscoroutinefunction(consume_sales_events)
