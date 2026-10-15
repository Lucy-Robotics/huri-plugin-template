# huri-module-example

A HuRI module, built and tested on its own: you need `huri-core`, the curated
events (`huri-events`) and this repository, not the rest of HuRI, a GPU or a
running pipeline.

<!-- template:start -->
## Starting a module from this template

1. On GitHub, click **Use this template** > **Create a new repository**
   (name it `huri-module-<name>`), then clone your new repository.
2. Rename the example to your module, once, on that fresh clone:

   ```sh
   ./rename.sh servo                       # your module's name, lowercase
   ```

   It renames `example`/`Example` everywhere (package, events package, topic
   namespace, entry point, manifest, this README), leaves `LICENSE` and
   `.github/` alone, and removes what only the template needs: this section,
   `tests/test_template.py` and the script itself. It refuses `huri` (the
   namespace of the curated events) and warns about the names of curated
   modules (`stt`, `tts`, `vad`, ...), which a server running both could not
   tell apart.
3. Commit, then follow the rest of this README.
<!-- template:end -->

## Installing and testing it

In a virtualenv, install HuRI's core and curated events, then the module with
its events, and test it:

```sh
python -m venv .venv && . .venv/bin/activate
python -m pip install \
  "huri-core[server] @ git+https://github.com/Lucy-Robotics/huri-core.git@<ref>" \
  "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-events"
./install.sh                            # picks requirements-{cpu,nvidia,amd}.txt for this machine
pytest                                  # tests/ runs the module with huri_core.testing
```

`./install.sh --variant cpu|nvidia|amd` chooses the variant instead of probing
the machine. `requirements-<variant>.txt` pins what the whole package needs on
that hardware. A package providing several modules, as some in `huri-modules`
do, can also pin one module's needs in `requirements-<variant>.<module>.txt`:
the `huri-modules` installer applies it only when that module is planned
(`install.sh` here installs the one module, from `requirements-<variant>.txt`). It installs with `python -m pip`, or `uv pip` in a virtualenv made
by `uv` without pip (set `PIP` to choose).

`<ref>` is a git ref of each repository: `dev` for now, a release tag once
there is one. The two repositories have their own versions and tags
(`huri-core` 0.4.0, `huri-modules` 0.1.0, ...); pick a pair from the
compatibility table in the
[huri-modules README](https://github.com/Lucy-Robotics/huri-modules#readme).
CI does the same through `HURI_CORE_REF` and `HURI_MODULES_REF`
(`.github/workflows/ci.yml`), and checks the style with `black`, `isort` and
`flake8` (installed by the `dev` extra).

Point `[project.urls]` in `pyproject.toml` at your repository.

## What is in it

| Path | What it is |
|---|---|
| `huri_example/module.py` | the module: a `Module` subclass with its input/output topics and `process()` |
| `huri_example/huri_module.toml` | its manifest, read by HuRI's startup check and the hub |
| `pyproject.toml` | the `huri.modules` entry point (`example = ...`), the dependencies and the project URLs |
| `events/` | the events the module introduces, as their own light distribution (`huri-events-example`) in their own topic namespace (`example.*`) — so a client can decode them without installing the module |
| `tests/` | the module tested alone (`ModuleHarness`), and the checks the server runs at startup |
| `requirements-{cpu,nvidia,amd}.txt`, `install.sh` | hardware-specific pins, and the script choosing them |
| `.github/workflows/ci.yml` | the same, on every push, against pinned `huri-core` and `huri-modules` refs |

The concepts (modules, events, topics, manifests, the server's checks) are
described in the [huri-core README](https://github.com/Lucy-Robotics/huri-core#readme).

## The module and its events: two distributions, one repository

The module depends on `huri-events-example`, which lives in `events/` and is on
no package index: pip finds it only when it is told where. So the module and
its events are installed **together, in one pip call**, as `install.sh` does
from a checkout. From GitHub, at a release tag:

```sh
python -m pip install \
  "huri-events-example @ git+https://github.com/<org>/<repo>.git@<tag>#subdirectory=events" \
  "huri-module-example @ git+https://github.com/<org>/<repo>.git@<tag>"
```

A client decoding `example.shout` installs only the events:

```sh
python -m pip install "huri-events-example @ git+https://github.com/<org>/<repo>.git@<tag>#subdirectory=events"
```

## Using it in HuRI

Installed on the server, the module is known by its entry point name:

```sh
HURI_MODULES=stt,tag,example ...        # the server's allow-list
```

```yaml
# client config
modules:
  example: { name: example, args: { exclamations: 2 } }
subscribe: [example.shout]
```

## When the module moves hardware

Set `requires = { actuation = true }` in the manifest (and `actuation = True` on
the class). The server then refuses to load it unless its operator lists it in
`HURI_ACTUATION_MODULES` as well as `HURI_MODULES`; document the module's
limits (ranges, rates) in this README.

## When the module needs a model

Run the model as a Ray Serve deployment and make the module a
`ModuleWithHandle` (`_handle_cls = YourDeployment`), calling
`await self._handle.method.remote(...)`; in tests, `LocalHandle(fake)` stands in
for the deployment. Import heavy libraries (torch, ...) inside the deployment,
not at module level: the server imports every enabled module to build the app.
[`packages/huri-module-stt`](https://github.com/Lucy-Robotics/huri-modules/tree/main/packages/huri-module-stt)
in huri-modules is a complete reference.

## Getting it listed

Tag the repository with the GitHub topic `huri-module` to be found by
`huri hub search`. The hub is not part of `huri-core`: it is the `huri-hub`
package of huri-modules, a plugin of `huri` (the `"huri.commands"` entry-point
group of `huri-core`), installed with

```sh
python -m pip install "huri-hub @ git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-hub"
huri hub search example
```

Until your module is verified, `huri hub install` installs it only when asked
explicitly (`--community`, or by URL); or install it with its events by hand,
as shown above.

To be listed as verified, open a pull request to
[huri-modules](https://github.com/Lucy-Robotics/huri-modules) adding an entry to
its `registry.toml` (see its
[ACCEPTANCE.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/ACCEPTANCE.md)).
A verified third-party module is pinned there at a release tag of your
repository, as a git submodule (`modules/<name>`), so tag your releases. The
entry also names the `events/` directory:

```toml
[[module]]
name = "example"
source = { git = "https://github.com/<org>/<repo>", tag = "<tag>", submodule = "modules/example", events = "events" }
```

so that `huri hub install` (from the tag) and huri-modules' CI (from the
reviewed submodule) install `events/` and the module in one pip call.

HuRI as a whole — what it is, how the repositories fit together — is presented
at [Lucy-Robotics/HuRI-landing](https://github.com/Lucy-Robotics/HuRI-landing).
