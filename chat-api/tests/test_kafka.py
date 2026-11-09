"""Tests for Kafka producer functions."""

from unittest.mock import patch

from services.kafka_producer import publish_message


@patch("services.kafka_producer.producer")
def test_publish_message_sends_and_flushes(mock_producer):
	topic = "test-topic"
	message = {"text": "hello"}

	publish_message(topic, message)

	mock_producer.send.assert_called_once_with(topic, value=message)
	mock_producer.flush.assert_called_once_with()

