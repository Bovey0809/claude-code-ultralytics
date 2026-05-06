---
generated: true
modelbox_commit: 125d1cd6b746cbfd410ac288a1e1f2e2664fb77e
modelbox_commit_date: 2026-05-06
---

# `output_broker`

**Devices:** cpu
**Group:** Output

## Purpose

Pluggable result sink. Routes pipeline output to Kafka, RocketMQ, an
HTTP endpoint, or a local file — configured by `broker_type`. Use when
the pipeline result should be consumed by an external system rather than
written to a video file.

## TOML config (`output_broker.toml`)

```toml
[base]
name = "output_broker"
device = "cpu"
version = "1.0.0"
type = "output_broker"

[config]
broker_type = "http"
broker_url = "http://localhost:9090/results"
```

## Ports

- **Input `in_data`:** json/bytes — Detection result or any serializable payload

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `broker_type` | yes | — | kafka | rocketmq | http | file |
| `broker_url` | yes | — | Kafka/RocketMQ broker URL, HTTP endpoint, or file path |

## Notes / gotchas

- For Kafka/RocketMQ, broker_url is the bootstrap server; add `topic` config
- For file output, broker_url is the output file path

## Upstream source

- `src/drivers/common/flowunit/output_broker/`

---
_Generated from modelbox@125d1cd6b746cbfd410ac288a1e1f2e2664fb77e (2026-05-06)._
