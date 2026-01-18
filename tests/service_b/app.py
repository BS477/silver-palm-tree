import os
import json
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import aio_pika

RABBIT_URL = os.environ.get("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672/")
STARTUP_RETRIES = int(os.environ.get("STARTUP_RETRIES", "12"))
STARTUP_BACKOFF = float(os.environ.get("STARTUP_BACKOFF", "1.0"))  # seconds

app = FastAPI(title="Service B - Enqueue AI jobs")

class CountIn(BaseModel):
    image_url: HttpUrl

async def try_connect_with_backoff(retries: int = STARTUP_RETRIES, backoff: float = STARTUP_BACKOFF):
    """Try to obtain a connection to RabbitMQ with exponential backoff."""
    attempt = 0
    while True:
        attempt += 1
        try:
            conn = await aio_pika.connect_robust(RABBIT_URL)
            return conn
        except Exception as exc:
            if attempt >= retries:
                raise
            wait = min(backoff * (2 ** (attempt - 1)), 30)
            print(f"[service_b] RabbitMQ not ready (attempt {attempt}/{retries}): {exc}. Retrying in {wait:.1f}s...")
            await asyncio.sleep(wait)

@app.on_event("startup")
async def startup():
    # ensure the queue exists but do not crash the container permanently if rabbit isn't ready yet
    try:
        conn = await try_connect_with_backoff()
    except Exception as exc:
        # Log and continue — enqueue endpoint will return 503 until broker is reachable
        print("[service_b] Warning: failed to connect to RabbitMQ during startup:", exc)
        return

    async with conn:
        channel = await conn.channel()
        await channel.declare_queue("person_count", durable=True)
        await channel.declare_queue("person_count_failed", durable=True)
        # Close connection (context manager will close)

@app.post("/count", status_code=202)
async def enqueue_count(payload: CountIn):
    message = {"image_url": str(payload.image_url)}
    try:
        # we attempt to connect but set a short timeout/backoff if broker is unreachable
        conn = await try_connect_with_backoff(retries=3, backoff=0.5)
    except Exception as exc:
        # Broker temporarily unavailable — inform client so they can retry
        raise HTTPException(status_code=503, detail="RabbitMQ is temporarily unavailable, try again later") from exc

    try:
        async with conn:
            channel = await conn.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key="person_count"
            )
    except Exception as exc:
        print("[service_b] Error publishing message to RabbitMQ:", exc)
        raise HTTPException(status_code=500, detail="Failed to enqueue job") from exc

    return {"status": "queued", "image_url": str(payload.image_url)}