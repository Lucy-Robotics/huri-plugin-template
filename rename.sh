#!/usr/bin/env bash
# Turns the template into your module:  ./rename.sh servo
# Renames example/Example in every file and directory: huri_example ->
# huri_servo, huri-module-example -> huri-module-servo, the "example." topic
# namespace -> "servo.", and so on. Run it once, on a fresh copy.
#
# Left alone: LICENSE and .github/ (their "example" is plain English, or
# nothing of the module's), git's and Python's own directories (.git, a
# virtualenv, caches, build outputs). tests/test_template.py tests the template
# itself, not your module: it is deleted.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
name="${1:?usage: rename.sh <name>   (lowercase, e.g. servo)}"
[[ "$name" =~ ^[a-z][a-z0-9_]*$ ]] || { echo "name must be lowercase [a-z0-9_]" >&2; exit 2; }
Name="$(tr '[:lower:]' '[:upper:]' <<<"${name:0:1}")${name:1}"
[[ -d huri_example ]] || { echo "already renamed (no huri_example/)" >&2; exit 1; }

rm -f tests/test_template.py
skip_dirs=(.git .github .venv venv .tox .pytest_cache __pycache__ build dist '*.egg-info')
grep_args=(-rlIZ --exclude=rename.sh --exclude=LICENSE)
for d in "${skip_dirs[@]}"; do grep_args+=("--exclude-dir=$d"); done
grep "${grep_args[@]}" -e example -e Example . |
  while IFS= read -r -d '' f; do
    sed -i -e "s/example/$name/g" -e "s/Example/$Name/g" "$f"
  done
mv huri_example "huri_$name"
mv events/huri_events_example "events/huri_events_$name"
echo "renamed to $name: edit huri_$name/module.py, its manifest and tests"
