from person_detection import get_image_url_people_count
import os
import asyncio
import json
import aiohttp
import aio_pika
from aio_pika import IncomingMessage
from datetime import datetime

RABBIT_URL = os.environ.get("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
SERVICE_A_URL = os.environ.get("SERVICE_A_URL", "http://service_a:8000/results")
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "5"))
PREFETCH_COUNT = int(os.environ.get("PREFETCH_COUNT", "1"))
CONNECT_RETRY_BACKOFF = float(os.environ.get("CONNECT_RETRY_BACKOFF", "1.0"))

async def count_persons(image_url: str) -> int:
    count = get_image_url_people_count(image_url)
    await asyncio.sleep(0.5)
    return count

async def requeue_with_backoff(channel, body, headers, attempts):
    headers = headers.copy()
    headers["x-attempts"] = attempts
    # publish with small delay (we do sleep in worker instead of relying on broker TTL)
    delay = min(2 ** attempts, 30)
    print(f"[worker] Backoff sleep {delay}s before republishing (attempt {attempts})")
    await asyncio.sleep(delay)
    await channel.default_exchange.publish(
        aio_pika.Message(body=body, headers=headers, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key="person_count"
    )

async def move_to_failed_queue(channel, body, headers, attempts):
    headers = headers.copy()
    headers["x-attempts"] = attempts
    await channel.default_exchange.publish(
        aio_pika.Message(body=body, headers=headers, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key="person_count_failed"
    )

async def handle_message(message: IncomingMessage):
    # Using message.process() will ack the message if no exception is raised
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body.decode())
            image_url = payload["image_url"]
            headers = message.headers or {}
            attempts = int(headers.get("x-attempts", 0)) + 1
        except Exception as exc:
            # malformed message -> ack and drop
            print("[worker] Malformed message, dropping:", exc)
            return

        print(f"[worker] Processing {image_url}, attempt {attempts}")
        count = await count_persons(image_url)
        result = {"image_url": image_url, "count": count, "timestamp": datetime.utcnow().isoformat()}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(SERVICE_A_URL, json=result, timeout=10) as resp:
                    if 200 <= resp.status < 300:
                        print("[worker] Successfully sent result to Service A")
                        return
                    else:
                        raise Exception(f"Non-2xx response from Service A: {resp.status}")
        except Exception as exc:
            print("[worker] Error sending to Service A:", exc)
            # We need a channel to republish or move to failed queue
            try:
                conn = await aio_pika.connect_robust(RABBIT_URL)
                async with conn:
                    channel = await conn.channel()
                    if attempts >= MAX_RETRIES:
                        print("[worker] Max attempts reached, moving to failed queue")
                        await move_to_failed_queue(channel, message.body, message.headers or {}, attempts)
                    else:
                        await requeue_with_backoff(channel, message.body, message.headers or {}, attempts)
            except Exception as pub_exc:
                # If we can't reach RabbitMQ to republish, raise so outer loop nacks and requeues the original
                print("[worker] Failed to republish to RabbitMQ:", pub_exc)
                raise

async def run_consumer():
    # persistent loop: try to connect, if fails wait and retry
    while True:
        try:
            print("[worker] Connecting to RabbitMQ...")
            conn = await aio_pika.connect_robust(RABBIT_URL)
            async with conn:
                channel = await conn.channel()
                await channel.set_qos(prefetch_count=PREFETCH_COUNT)
                queue = await channel.declare_queue("person_count", durable=True)
                print("[worker] Connected and waiting for messages...")
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        try:
                            await handle_message(message)
                        except Exception as exc:
                            # If something went wrong during handling and we could not republish, nack with requeue
                            try:
                                await message.nack(requeue=True)
                            except Exception:
                                pass
                            print("[worker] Unhandled error while handling message:", exc)
        except Exception as exc:
            print(f"[worker] Connection to RabbitMQ failed: {exc}. Retrying in {CONNECT_RETRY_BACKOFF}s...")
            await asyncio.sleep(CONNECT_RETRY_BACKOFF)

def main():
    asyncio.run(run_consumer())

if __name__ == "__main__":
    print("Starting consumer worker...")
    main()
