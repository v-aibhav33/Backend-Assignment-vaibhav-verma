from datetime import datetime
from app.models import get_db

def insert_message(data):
    conn = get_db()
    try:
        conn.execute("""
        INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["message_id"],
            data["from"],
            data["to"],
            data["ts"],
            data.get("text"),
            datetime.utcnow().isoformat() + "Z"
        ))
        conn.commit()
        return "created"
    except:
        return "duplicate"