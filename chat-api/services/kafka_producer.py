"""kafka_producer.py - Kafka producer service for the live chat API application"""

from kafka import KafkaProducer
import json
import os

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "chat-messages")

producer = None

def get_producer():
    """Connect to Kafka the first time it's needed, then reuse the connection."""
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            max_block_ms=5000,   # give up after 5 seconds if Kafka is down
        )
    return producer

def publish_message(message):
    producer = get_producer()
    #publishes message to the kafka topic
    producer.send(KAFKA_TOPIC, message)
    producer.flush(timeout=5)
