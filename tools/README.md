# tools/

Maintainer tooling for the `modelbox` skill.

## Files

| File | Purpose |
|------|---------|
| `modelbox-flowunits.yml` | Allowlist: 19 flowunits, pinned upstream SHA, all metadata |
| `modelbox-skill-prelude.md` | Hand-written SKILL.md sections (non-catalog) |
| `modelbox-skill-recipes.md` | Four pipeline recipe skeletons |
| `build-modelbox-skill.py` | Generator: reads YAML + prelude + recipes → `skills/modelbox/` |
| `test-modelbox-skill.py` | Validator: six-section linter, parity, TOML validity, pin record |

## Regenerate skill files

```bash
# 1. Clone upstream at pinned commit (or update to a new one)
COMMIT=$(python3 -c "import yaml; print(yaml.safe_load(open('tools/modelbox-flowunits.yml'))['modelbox_commit'])")
git clone --depth=200 https://github.com/modelbox-ai/modelbox.git /tmp/modelbox-upstream
git -C /tmp/modelbox-upstream checkout "$COMMIT"

# 2. Generate
python3 tools/build-modelbox-skill.py \
    --modelbox-repo /tmp/modelbox-upstream \
    --commit "$COMMIT" \
    --out skills/modelbox/

# 3. Validate
python3 tools/test-modelbox-skill.py skills/modelbox/
```

## Bump the pinned commit manually

Edit `modelbox_commit` and `modelbox_commit_date` in `tools/modelbox-flowunits.yml`, then re-run steps 2 and 3 above.

## Add a new flowunit

1. Add an entry to `tools/modelbox-flowunits.yml` following the existing schema.
2. Regenerate and validate.
3. The new flowunit appears in the catalog automatically.

## CI auto-bump

`.github/workflows/modelbox-bump.yml` runs daily and opens a PR when upstream HEAD diverges from the pin. The PR includes a diff summary. Maintainers review and merge; the workflow never auto-merges.
