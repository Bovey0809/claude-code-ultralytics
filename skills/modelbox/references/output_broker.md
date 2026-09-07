---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
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
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
