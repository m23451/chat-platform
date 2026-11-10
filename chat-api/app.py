""" app.py - main entry point for the chat API application """

from flask import Flask, request, jsonify, render_template
from services.kafka_producer import publish_message
import db
import os

KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "chat-messages")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/messages", methods=["POST"])
def send_message():
    data = request.get_json()
    if (not data
            or not str(data.get("author", "")).strip()
            or not str(data.get("text", "")).strip()):
        return jsonify({"error": "missing fields."}), 400

    message = db.save_message(
        author=data["author"],
        text=data["text"],
        client_id=data.get("clientId")
    )

    try:
        publish_message(message)
    except Exception as e:
        app.logger.warning("Kafka publish failed: %s", e)
    return jsonify(message), 201


#def get_messages():
    # Placeholder for retrieving messages from Kafka
    #return jsonify({"messages": []}), 200"""

#This will gets the history of the messages ge=minimum amount, le=maximum amount
@app.route("/api/messages", methods=["GET"])
def history():
    limit = request.args.get("limit", default=50, type=int)
    before = request.args.get("before", default=None, type=int)
    if limit is None or not 1 <= limit <= 200:
        return jsonify({"error": "limit must be between 1 and 200"}), 400
    return jsonify(db.load_history(limit, before))


@app.route("/kubernetes/liveness", methods=["GET"])
def liveness():
    return jsonify({"status": "UP"})

@app.route("/kubernetes/ready", methods=["GET"])
def ready():
    if db.is_healthy():
        return jsonify({"status": "UP"})
    return jsonify({"status": "DOWN"}), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
