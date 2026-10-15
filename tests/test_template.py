"""The template itself stays a working starting point.

This file tests the template, not the module made from it: rename.sh deletes it.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from huri_core.core.manifest import load_manifest
from huri_core.testing import ModuleHarness

ROOT = Path(__file__).resolve().parents[1]

# What a copy of the template leaves behind: never part of a fresh clone.
_LOCAL = shutil.ignore_patterns(
    ".git", ".venv", "__pycache__", ".pytest_cache", "*.egg-info", "build", "dist"
)


@pytest.fixture
def template_on_path(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "events"))
    monkeypatch.syspath_prepend(str(ROOT))
    yield
    for name in [
        m for m in sys.modules if m.startswith(("huri_example", "huri_events_example"))
    ]:
        del sys.modules[name]


@pytest.fixture
def renamed(tmp_path):
    """A copy of the template renamed to "servo" (never rename this checkout)."""
    copy = tmp_path / "huri-module-servo"
    shutil.copytree(ROOT, copy, ignore=_LOCAL)
    # Stand-ins for a virtualenv and a git directory: rename.sh must not touch
    # them.
    for d in (".venv", ".git"):
        (copy / d).mkdir()
        (copy / d / "example.txt").write_text("example\n")
    subprocess.run(
        ["bash", str(copy / "rename.sh"), "servo"], check=True, capture_output=True
    )
    return copy


def test_the_example_module_works(template_on_path):
    from huri_events.speech import Transcript

    from huri_events_example import Shout
    from huri_example.module import Shouter

    out = ModuleHarness(Shouter).run(Transcript("hi", True))
    assert out == [Shout("HI!")]


def test_its_manifest_matches_the_module(template_on_path):
    from huri_example.module import Shouter

    manifest = load_manifest(ROOT / "huri_example" / "huri_module.toml")
    assert manifest.name == "example"
    assert (manifest.input.topic, manifest.output.topic) == (
        Shouter.input_type,
        Shouter.output_type,
    )
    for port, cls in (
        (manifest.input, Shouter.input_event),
        (manifest.output, Shouter.output_event),
    ):
        assert port.event == f"{cls.__module__}:{cls.__qualname__}"


def test_rename_leaves_no_trace_of_the_example(renamed):
    assert (renamed / "huri_servo" / "module.py").is_file()
    assert (renamed / "events" / "huri_events_servo" / "__init__.py").is_file()
    assert not (renamed / "tests" / "test_template.py").exists()
    # The module itself is renamed: its entry point and manifest.
    pyproject = (renamed / "pyproject.toml").read_text()
    assert 'servo = "huri_servo.module:Shouter"' in pyproject
    assert 'name = "huri-module-servo"' in pyproject
    assert 'name = "servo"' in (renamed / "huri_servo" / "huri_module.toml").read_text()
    leftovers = subprocess.run(
        [
            "grep",
            "-rlI",
            "-i",
            "example",
            "--exclude=rename.sh",
            "--exclude=LICENSE",
            "--exclude-dir=.git",
            "--exclude-dir=.venv",
            str(renamed),
        ],
        capture_output=True,
        text=True,
    ).stdout.split()
    assert leftovers == []


def test_rename_leaves_license_ci_and_local_dirs_alone(renamed):
    for path in ("LICENSE", ".github/workflows/ci.yml"):
        assert (renamed / path).read_bytes() == (ROOT / path).read_bytes(), path
    for d in (".venv", ".git"):
        assert (renamed / d / "example.txt").read_text() == "example\n"


def test_the_renamed_module_is_consistent(renamed):
    """The renamed copy imports, runs, and still matches its manifest."""
    probe = """
from huri_core.core.manifest import load_manifest
from huri_core.testing import ModuleHarness
from huri_events.speech import Transcript
from huri_events_servo import Shout
from huri_servo.module import Shouter

assert ModuleHarness(Shouter).run(Transcript("hi", True)) == [Shout("HI!")]
m = load_manifest("huri_servo/huri_module.toml")
assert (m.name, m.input.topic, m.output.topic) == (
    "servo", Shouter.input_type, Shouter.output_type
), m
assert Shouter.output_type == "servo.shout"
assert m.output.event == "huri_events_servo:Shout"
"""
    subprocess.run(
        [sys.executable, "-c", probe],
        cwd=renamed,
        env={"PYTHONPATH": f"{renamed}:{renamed / 'events'}"},
        check=True,
    )


@pytest.mark.parametrize("script", ["install.sh", "rename.sh"])
def test_scripts_parse(script):
    subprocess.run(["bash", "-n", str(ROOT / script)], check=True)
