#!/usr/bin/env bash
# Turns the template into your module:  ./rename.sh servo
# Renames example/Example in every file and directory: example -> servo,
# example_events -> servo_events, example-events -> servo-events, the
# "example." topic namespace -> "servo.", and so on. Run it once, on a fresh copy.
#
# Left alone: LICENSE and .github/ (their "example" is plain English, or
# nothing of the module's), git's and Python's own directories (.git, a
# virtualenv, caches, build outputs). Removed, being the template's own: the
# README's bootstrap section (between the template:start/end markers),
# tests/test_template.py (it tests the template, not your module) and this
# script.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
self="$(basename "${BASH_SOURCE[0]}")"
name="${1:?usage: rename.sh <name>   (lowercase, e.g. servo)}"
[[ "$name" =~ ^[a-z][a-z0-9_]*$ ]] || { echo "name must be lowercase [a-z0-9_]" >&2; exit 2; }
if [[ "$name" == huri ]]; then
  echo "\"huri\" is the namespace of the curated events (huri.*): choose another name" >&2
  exit 2
fi
# The name becomes a top-level package, so it must not shadow HuRI's or Python's own.
if [[ "$name" == huri_* ]]; then
  echo "\"$name\" would shadow a HuRI package (huri_*): choose another name" >&2
  exit 2
fi
if python3 -c 'import sys; sys.exit(sys.argv[1] not in getattr(sys, "stdlib_module_names", ()))' "$name" 2>/dev/null; then
  echo "\"$name\" is a Python standard library module: choose another name" >&2
  exit 2
fi
# The curated modules of huri-modules (its registry.toml): a server running
# both could not tell them apart.
curated=" stt tag tts tts_cosyvoice vad emo eag rag qag mov "
if [[ "$curated" == *" $name "* ]]; then
  echo "warning: \"$name\" is the name of a curated HuRI module; yours would clash with it" >&2
fi
Name="$(tr '[:lower:]' '[:upper:]' <<<"${name:0:1}")${name:1}"
# The package becomes a top-level folder named after the module.
if [[ -e "$name" ]]; then
  echo "\"$name\" is already a folder of this repository: choose another name" >&2
  exit 2
fi
[[ -d example ]] || { echo "already renamed (no example/)" >&2; exit 1; }

sed -i '/<!-- template:start -->/,/<!-- template:end -->/d' README.md
readme="$(cat -s README.md)" && printf '%s\n' "$readme" >README.md # one blank line left
rm -f tests/test_template.py
skip_dirs=(.git .github .venv venv .tox .pytest_cache __pycache__ build dist '*.egg-info')
grep_args=(-rlIZ "--exclude=$self" --exclude=LICENSE)
for d in "${skip_dirs[@]}"; do grep_args+=("--exclude-dir=$d"); done
grep "${grep_args[@]}" -e example -e Example . |
  while IFS= read -r -d '' f; do
    sed -i -e "s/example/$name/g" -e "s/Example/$Name/g" "$f"
  done
mv example "$name"
mv events/example_events "events/${name}_events"
rm -f -- "$self"
echo "renamed to $name: edit $name/module.py, its manifest and tests, then commit"
