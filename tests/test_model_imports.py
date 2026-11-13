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


# An import hook, not `sys.modules[name] = None`: a library that tests
# `name in sys.modules` (scipy does for torch) must see it as absent.
HIDE = """import sys
class Hide:
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] in HIDDEN:
            raise ModuleNotFoundError(f"{name} is hidden", name=name)
sys.meta_path.insert(0, Hide())
"""


def test_the_module_imports_with_its_model_libraries_hidden():
    # The module, not a class: its top-level imports are what is checked.
    code = f"HIDDEN = {MODEL_LIBRARIES!r}\n{HIDE}import huri_example.module\n"
    # cwd=ROOT: the module of this checkout, before any installed copy.
    run = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True
    )
    assert run.returncode == 0, (
        f"huri_example/module.py imports one of {MODEL_LIBRARIES} when it is "
        f"imported; import it inside the method that uses it:\n{run.stderr}"
    )
