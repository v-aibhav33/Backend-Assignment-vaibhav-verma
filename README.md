## How to Run
make up

## Endpoints
POST /webhook
GET /messages
GET /stats
GET /metrics

## Design Decisions
- SQLite used for simplicity
- message_id as primary key for idempotency
- HMAC SHA256 for webhook security

## Setup Used
VS Code + ChatGPT
