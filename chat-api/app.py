""" app.py - main entry point for the chat API application """

from flask import Flask, request, jsonify, render_template
from services.kafka_producer import publish_message

from services.database import get_messages, save_message

KAFKA_BROKER_URL = 'localhost:9092' 
KAFKA_TOPIC = 'chat-messages'

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/messages", methods=["POST"])
def send_message():
    data = request.get_json()
    """ if (not data 
        or "username" not in data 
        or "text" not in data):
            return jsonify({"error": "missing fields."}), 400

    publish_message(data)"""

    publish_message(data)

    save_message(
        username=data["username"],
        text=data["text"],
        client_id=data["client_id"]
    )

    return jsonify({"status": "Message sent to Kafka"}), 200

@app.route("/api/messages", methods=["GET"])

#def get_messages():
    # Placeholder for retrieving messages from Kafka
    #return jsonify({"messages": []}), 200"""

def history():

    return jsonify(get_messages())


if __name__ == "__main__":
    app.run(debug=True)
