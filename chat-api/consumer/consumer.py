from kafka import KafkaConsumer
import json

from services.database import save_message

KAFKA_BROKER_URL = 'localhost:9092' 
KAFKA_TOPIC = 'chat-messages'

consumer = KafkaConsumer(
    "chat-messages",
    bootstrap_servers=KAFKA_BROKER_URL,
    auto_offset_reset='latest', #kafka reads latest messages from the topic
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

print("Kafka consumer is running and listening to topic", KAFKA_TOPIC)

for kafka_message in consumer:
    
    data = kafka_message.value
    print("Recieved message:", data)

    saved = save_message(
        username=data["username"],
        text=data["text"],
        client_id=data["client_id"]
    )

    print("Saved:",saved)