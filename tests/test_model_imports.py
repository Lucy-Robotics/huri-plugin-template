"""The server's head node imports every enabled module to build the app,
whatever its hardware: it may have no GPU and none of your model libraries. So
module.py imports them lazily, inside the methods that use them."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Your module's model libraries, as you import them (e.g. "torch",
# "transformers", "faster_whisper"): add each one here.
MODEL_LIBRARIES: list[str] = []


def test_the_module_imports_with_its_model_libraries_hidden():
    hide = "".join(f"sys.modules[{name!r}] = None\n" for name in MODEL_LIBRARIES)
    code = f"import sys\n{hide}from huri_example.module import Shouter\n"
    # cwd=ROOT: the module of this checkout, before any installed copy.
    run = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
    )
    assert run.returncode == 0, (
        f"huri_example/module.py imports one of {MODEL_LIBRARIES} when it is "
        f"imported; import it inside the method that uses it:\n{run.stderr}"
    )
