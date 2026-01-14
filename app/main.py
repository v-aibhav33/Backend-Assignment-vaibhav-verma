from fastapi import FastAPI, Request, HTTPException
from uuid import uuid4
import time, hmac, hashlib

from app.config import WEBHOOK_SECRET, is_ready
from app.models import init_db, get_db
from app.storage import insert_message
from app.logging_utils import log_event
from app.metrics import inc_http, inc_webhook, render_metrics

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()



@app.get("/health/live")
def live():
    return {"status": "alive"}

@app.get("/health/ready")
def ready():
    if not is_ready():
        raise HTTPException(status_code=503)
    try:
        get_db().execute("SELECT 1")
        return {"status": "ready"}
    except:
        raise HTTPException(status_code=503)



def verify_signature(secret, body, signature):
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def webhook(request: Request):
    start = time.time()
    request_id = str(uuid4())
    raw_body = await request.body()

    signature = request.headers.get("X-Signature")
    if not signature or not verify_signature(WEBHOOK_SECRET, raw_body, signature):
        inc_webhook("invalid_signature")
        log_event({
            "level": "ERROR",
            "request_id": request_id,
            "method": "POST",
            "path": "/webhook",
            "status": 401,
            "latency_ms": 0,
            "result": "invalid_signature"
        })
        raise HTTPException(401, detail="invalid signature")

    data = await request.json()
    result = insert_message(data)
    inc_webhook(result)

    latency = int((time.time() - start) * 1000)
    log_event({
        "level": "INFO",
        "request_id": request_id,
        "method": "POST",
        "path": "/webhook",
        "status": 200,
        "latency_ms": latency,
        "message_id": data["message_id"],
        "dup": result == "duplicate",
        "result": result
    })

    inc_http("/webhook", 200)
    return {"status": "ok"}


@app.get("/messages")
def messages(limit: int = 50, offset: int = 0):
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    rows = conn.execute("""
        SELECT message_id, from_msisdn as "from", to_msisdn as "to", ts, text
        FROM messages
        ORDER BY ts ASC, message_id ASC
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()

    return {
        "data": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset
    }



@app.get("/stats")
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    senders = conn.execute("""
        SELECT from_msisdn as "from", COUNT(*) as count
        FROM messages
        GROUP BY from_msisdn
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()

    first = conn.execute("SELECT MIN(ts) FROM messages").fetchone()[0]
    last = conn.execute("SELECT MAX(ts) FROM messages").fetchone()[0]

    return {
        "total_messages": total,
        "senders_count": len(senders),
        "messages_per_sender": [dict(r) for r in senders],
        "first_message_ts": first,
        "last_message_ts": last
    }



@app.get("/metrics")
def metrics():
    return render_metrics()
