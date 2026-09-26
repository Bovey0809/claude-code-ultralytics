---
generated: true
modelbox_commit: faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d
modelbox_commit_date: 2024-03-13
---

# `meta_mapping`

**Devices:** cpu
**Group:** Utility

## Purpose

Field-projection flowunit. Renames, reorders, or drops metadata fields
between flowunits. Useful when one flowunit emits a field under a name
that the next expects under a different name, without writing a custom
flowunit. Configure `mappings` as a JSON object of {new_name: old_name}.

## TOML config (`meta_mapping.toml`)

```toml
[base]
name = "meta_mapping"
device = "cpu"
version = "1.0.0"
type = "meta_mapping"

[config]
mappings = "{\"out_key\": \"in_key\"}"
```

## Ports

- **Input `in_data`:** any — Data item with fields to remap
- **Output `out_data`:** any — Data item with remapped fields

## Config keys

| Key | Required | Default | Notes |
|-----|----------|---------|-------|
| `mappings` | yes | {} | JSON object {new_field_name -> old_field_name} |

## Notes / gotchas

- Fields not mentioned in mappings are passed through unchanged
- Use to bridge naming differences without writing a custom C++ flowunit

## Upstream source

- `src/drivers/common/flowunit/meta_mapping/`

---
_Generated from modelbox@faa1e931a464fb3c30e6a9988cc4a3acd6aaa26d (2024-03-13)._
