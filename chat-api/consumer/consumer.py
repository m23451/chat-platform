import json
import logging
import os
import threading
import time
from kafka import KafkaConsumer
import chatSocket


log = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "chat-messages")

def _run():
    print("Kafka consumer is running and listening to topic", KAFKA_TOPIC)
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKER_URL,
                group_id=None,                 # no group: EVERY pod gets EVERY message
                auto_offset_reset="latest",    # only new messages, not old ones
                value_deserializer=lambda b: json.loads(b.decode("utf-8")),
            )
            log.warning("Kafka consumer connected to %s", KAFKA_BROKER_URL)
            for record in consumer:
                chatSocket.broadcast(record.value)
        except Exception as e:
            log.warning("Kafka consumer error, retrying in 5s: %s", e)
            time.sleep(5)


def start():
    """Run the consumer in the background so it doesn't block the API."""
    threading.Thread(target=_run, daemon=True, name="kafka-consumer").start()