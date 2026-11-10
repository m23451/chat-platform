"""Tests for Kafka producer functions."""

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


import pytest
from unittest.mock import patch
from services.kafka_producer import publish_message



@patch("services.kafka_producer.producer")
def test_publish_message_sends_and_flushes(
    mock_producer
):

    message = {
        "text": "hello"
    }

    publish_message(message)

    mock_producer.send.assert_called_once()
    mock_producer.flush.assert_called_once()