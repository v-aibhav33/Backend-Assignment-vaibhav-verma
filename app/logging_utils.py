import json
import logging
from datetime import datetime

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def log_event(data):
    data["ts"] = datetime.utcnow().isoformat() + "Z"
    logger.info(json.dumps(data))