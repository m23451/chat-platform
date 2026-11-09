"""kafka_producer.py - Kafka producer service for the live chat API application"""

from kafka import KafkaProducer
import json

KAFKA_BROKER_URL = 'localhost:9092' 
KAFKA_TOPIC = 'chat-messages'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_message(message):
    #publishes message to the kafka topic
    producer.send(KAFKA_TOPIC, message)
