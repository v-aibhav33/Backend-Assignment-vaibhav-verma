http_requests = {}
webhook_requests = {}

def inc_http(path, status):
    key = (path, status)
    http_requests[key] = http_requests.get(key, 0) + 1

def inc_webhook(result):
    webhook_requests[result] = webhook_requests.get(result, 0) + 1

def render_metrics():
    lines = []
    for (path, status), count in http_requests.items():
        lines.append(
            f'http_requests_total{{path="{path}",status="{status}"}} {count}'
        )
    for result, count in webhook_requests.items():
        lines.append(
            f'webhook_requests_total{{result="{result}"}} {count}'
        )