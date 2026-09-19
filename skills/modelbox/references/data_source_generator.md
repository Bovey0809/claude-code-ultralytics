---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `data_source_generator`

**Devices:** cpu
**Group:** Input

## Purpose

Generic file/directory source. Replays file paths (or directory globs)
into a stream, one path per data item. Use for image directories or when
you need fine-grained control over batching and retries. Prefer
`video_input` for single video files.

## TOML config (`data_source_generator.toml`)

```toml
[base]
name = "data_source_generator"
device = "cpu"
version = "1.0.0"
type = "data_source_generator"

[config]
source_url = "${input_path}"
retry_count = 3
retry_interval = 1
```

## Ports

- **Output `out_data`:** string — File path emitted for each item in the source

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `source_url` | yes | — | File path, directory glob, or URL |
| `retry_count` | no | 3 | Number of retries on source open failure |
| `retry_interval` | no | 1 | Seconds between retries |

## Notes / gotchas

- For video files use video_input instead (simpler wiring)
- Directory globs emit one path per matching file in lexicographic order

## Upstream source

- `src/drivers/common/flowunit/data_source_generator/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
