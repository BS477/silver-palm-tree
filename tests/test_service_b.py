import asyncio
import json
import aio_pika
import pytest
import os
from fastapi.testclient import TestClient

from service_b.app import app

SERVICE_A_URL = os.environ.get("SERVICE_A_URL", "localhost:8000")
SERVICE_B_URL = os.environ.get("SERVICE_B_URL", "localhost:8001")

QUEUE_NAME = "person_count"
RABBIT_URL = os.environ.get("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672")

client = TestClient(app)

@pytest.mark.integration
def test_enqueue_really_publishes_to_rabbit():
    payload = {"image_url": "https://cdn.wikibound.info/1/16/EB_banner1.jpg"}

    # Call the API
    response = client.post(SERVICE_B_URL+"/count", json=payload)

    assert response.status_code == 202
    assert response.json()["status"] == "queued"

    # Call the API 10 more times so consumer doesn't parse the entire thing immediately
    for i in range(10):
        response = client.post(SERVICE_B_URL+"/count", json=payload)

    # Verify message was actually published
    asyncio.run(assert_message_in_queue(payload))


async def assert_message_in_queue(expected_payload):
    connection = await aio_pika.connect_robust(RABBIT_URL)

    async with connection:
        channel = await connection.channel()

        # Ensure queue exists
        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True
        )

        # Try to get a message (non-blocking)
        message = await queue.get(timeout=5)

        assert message is not None

        async with message.process():
            body = json.loads(message.body.decode())
            assert body == expected_payload
