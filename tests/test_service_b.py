import asyncio
import json
import aio_pika
import pytest
from fastapi.testclient import TestClient

from service_b.app import app

QUEUE_NAME = "image_jobs"

client = TestClient(app)

@pytest.mark.integration
def test_enqueue_really_publishes_to_rabbit():
    payload = {"image_url": "http://example.org/pic.jpg"}

    # Call the API
    response = client.post("/count", json=payload)

    assert response.status_code == 202
    assert response.json()["status"] == "queued"

    # Verify message was actually published
    asyncio.run(assert_message_in_queue(payload))


async def assert_message_in_queue(expected_payload):
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost/"
    )

    async with connection:
        channel = await connection.channel()

        # Ensure queue exists
        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True
        )

        # Try to get a message (non-blocking)
        message = await queue.get(timeout=2)

        assert message is not None

        async with message.process():
            body = json.loads(message.body.decode())
            assert body == expected_payload
