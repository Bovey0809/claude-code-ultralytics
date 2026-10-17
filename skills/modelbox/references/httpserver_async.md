---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `httpserver_async`

**Devices:** cpu
**Group:** Input

## Purpose

Async HTTP server edge. Exposes an HTTP endpoint; each inbound request
becomes one pipeline data item. Pairs with a reply port on a downstream
flowunit to send the HTTP response. Use for request/reply inference APIs.

## TOML config (`httpserver_async.toml`)

```toml
[base]
name = "httpserver_async"
device = "cpu"
version = "1.0.0"
type = "httpserver_async"

[config]
endpoint = "/api/detect"
port = 8080
max_requests = 10
```

## Ports

- **Input `in_reply`:** json/bytes — HTTP response body; wire from final result flowunit
- **Output `out_request`:** bytes — Raw HTTP request body for each inbound call

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `endpoint` | yes | — | URL path to listen on, e.g. /api/detect |
| `port` | yes | 8080 | TCP port |
| `max_requests` | no | 10 | Max in-flight concurrent requests |

## Notes / gotchas

- The reply port must be wired back from the last flowunit in the pipeline
- One request = one pipeline execution; async means requests do not block each other

## Upstream source

- `src/drivers/common/flowunit/httpserver_async/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
