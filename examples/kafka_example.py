"""
Kafka integration example for iot-logging-schemas.

This example shows how to log both Kafka message production and consumption.
Context fields are automatically injected by StructuredJsonFormatter.
"""

import json
import logging
import time

from confluent_kafka import Consumer, KafkaError, Producer

from iot_logging import StructuredJsonFormatter

# ===== Configure logging =====

logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

logger = logging.getLogger(__name__)


# ===== Kafka Consumer Configuration =====


def create_kafka_consumer(topic, consumer_group):
    """Create and configure Kafka consumer."""
    conf = {
        "bootstrap.servers": "localhost:9092",
        "group.id": consumer_group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    return Consumer(conf), topic


# ===== Message Processing =====


def process_telemetry_message(msg_value, partition, offset):
    """
    Process a telemetry message from Kafka.
    """
    start_time = time.time()

    logger.info(
        "Processing telemetry message",
        extra={
            "topic": "telemetry.raw",
            "consumer_group": "analytics-processor",
            "partition": partition,
            "offset": offset,
            "status": "processing",
        },
    )

    try:
        # Parse message (example)
        device_id = msg_value.get("device_id")
        temperature = msg_value.get("temperature")

        # Simulate downstream processing
        logger.info(
            "Storing telemetry data",
            extra={
                "device_id": device_id,
                "temperature": temperature,
                "operation": "store_timeseries",
            },
        )

        # Log success
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Message processed successfully",
            extra={
                "topic": "telemetry.raw",
                "consumer_group": "analytics-processor",
                "partition": partition,
                "offset": offset,
                "status": "success",
                "processing_duration_ms": duration_ms,
                "device_id": device_id,
            },
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Message processing failed",
            extra={
                "topic": "telemetry.raw",
                "consumer_group": "analytics-processor",
                "partition": partition,
                "offset": offset,
                "status": "error",
                "processing_duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise


def process_events_message(msg_value, partition, offset):
    """
    Process an event message from Kafka.
    """
    start_time = time.time()

    logger.info(
        "Processing device event",
        extra={
            "topic": "device.events",
            "consumer_group": "event-processor",
            "partition": partition,
            "offset": offset,
            "status": "processing",
        },
    )

    try:
        event_type = msg_value.get("type")
        device_id = msg_value.get("device_id")

        # Route event to appropriate handler
        logger.info(
            "Routing event",
            extra={
                "event_type": event_type,
                "device_id": device_id,
                "operation": "route_event",
            },
        )

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "Event processed successfully",
            extra={
                "topic": "device.events",
                "consumer_group": "event-processor",
                "partition": partition,
                "offset": offset,
                "status": "success",
                "processing_duration_ms": duration_ms,
                "event_type": event_type,
            },
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Event processing failed",
            extra={
                "topic": "device.events",
                "consumer_group": "event-processor",
                "partition": partition,
                "offset": offset,
                "status": "error",
                "processing_duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise


# ===== Consumer Loop =====


def run_consumer(topic, consumer_group):
    """Run Kafka consumer loop."""
    consumer, _ = create_kafka_consumer(topic, consumer_group)

    logger.info(
        "Consumer started",
        extra={
            "service_name": "kafka_consumer",
            "component": topic,
            "consumer_group": consumer_group,
            "event": "consumer_started",
        },
    )

    consumer.subscribe([topic])

    try:
        while True:
            # Poll for messages
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(
                        "Partition EOF reached",
                        extra={
                            "topic": msg.topic(),
                            "partition": msg.partition(),
                            "offset": msg.offset(),
                        },
                    )
                else:
                    logger.error(
                        "Consumer error",
                        extra={
                            "error_type": type(msg.error()).__name__,
                            "error_message": str(msg.error()),
                        },
                    )
                continue

            # Process message based on topic
            try:
                import json

                msg_value = json.loads(msg.value().decode("utf-8"))

                if topic == "telemetry.raw":
                    process_telemetry_message(msg_value, msg.partition(), msg.offset())
                elif topic == "device.events":
                    process_events_message(msg_value, msg.partition(), msg.offset())

            except Exception as e:
                logger.error(
                    "Message deserialization failed",
                    extra={
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )

    except KeyboardInterrupt:
        logger.info(
            "Consumer shutting down",
            extra={
                "service_name": "kafka_consumer",
                "component": topic,
                "event": "consumer_shutdown",
            },
        )
    finally:
        consumer.close()


# ===== Kafka Producer =====


def produce_telemetry_message(device_id, temperature, humidity):
    """
    Produce a telemetry message to Kafka and log it.
    """
    producer = Producer({"bootstrap.servers": "localhost:9092"})
    start_time = time.time()

    try:
        message = {
            "device_id": device_id,
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": time.time(),
        }

        # Send message
        producer.produce(
            topic="telemetry.raw",
            key=device_id.encode("utf-8"),
            value=json.dumps(message).encode("utf-8"),
        )
        producer.flush()

        duration_ms = (time.time() - start_time) * 1000

        # Log successful send
        logger.info(
            "Telemetry message sent",
            extra={
                "topic": "telemetry.raw",
                "message_key": device_id,
                "status": "success",
                "duration_ms": duration_ms,
            },
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            "Failed to send telemetry message",
            extra={
                "topic": "telemetry.raw",
                "message_key": device_id,
                "status": "error",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise

    finally:
        producer.flush()


# ===== Run example =====

if __name__ == "__main__":
    # Run consumers for multiple topics
    import threading

    telemetry_thread = threading.Thread(
        target=run_consumer, args=("telemetry.raw", "analytics-processor")
    )
    events_thread = threading.Thread(
        target=run_consumer, args=("device.events", "event-processor")
    )

    telemetry_thread.start()
    events_thread.start()

    telemetry_thread.join()
    events_thread.join()
