""" app.py - main entry point for the chat API application """

from flask import Flask, request, jsonify, render_template
from services.kafka_producer import publish_message
import db
import os
import asyncio

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "chat-messages")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("chat-api/templates/index.html")

#asynch change here for endpoint
@app.route("/api/messages", methods=["POST"])
async def send_message():
    data = request.get_json()
    if (not data
            or not str(data.get("author", "")).strip()
            or not str(data.get("text", "")).strip()):
        return jsonify({"error": "missing fields."}), 400

    #to make asynch
    message = await asyncio.to_thread(
        db.save_message,
        author=data["author"],
        text=data["text"],
        client_id=data.get("clientId")
    )

    try:
        await asyncio.to_thread(publish_message, message)
    except Exception as e:
        app.logger.warning("Kafka publish failed: %s", e)
    return jsonify(message), 201


#def get_messages():
    # Placeholder for retrieving messages from Kafka
    #return jsonify({"messages": []}), 200"""

#This will gets the history of the messages ge=minimum amount, le=maximum amount
@app.route("/api/messages", methods=["GET"])
async def history():
    limit = request.args.get("limit", default=50, type=int)
    before = request.args.get("before", default=None, type=int)
    if limit is None or not 1 <= limit <= 200:
        return jsonify({"error": "limit must be between 1 and 200"}), 400

    messages = await asyncio.to_thread(db.load_history, limit, before)
    return jsonify(messages)


@app.route("/kubernetes/liveness", methods=["GET"])
def liveness():
    return jsonify({"status": "UP"})


#async endpoint
@app.route("/kubernetes/ready", methods=["GET"])
async def ready():
    healthy = await asyncio.to_thread(db.is_healthy)
    if healthy:
        return jsonify({"status": "UP"})
    return jsonify({"status": "DOWN"}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

