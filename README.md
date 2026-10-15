# huri-module-example

A starting point for a new HuRI module, built and tested on its own: you need
`huri-core`, the curated events (`huri-events`) and this repository, not the
rest of HuRI, a GPU or a running pipeline.

## Starting a module from it

1. On GitHub, click **Use this template** > **Create a new repository**
   (name it `huri-module-<name>`), then clone your new repository.
2. Rename the example to your module, once, on that fresh clone:

   ```sh
   ./rename.sh servo                       # your module's name, lowercase
   ```

   It renames `example`/`Example` everywhere (package, events package, topic
   namespace, entry point, manifest, this README), leaves `LICENSE` and
   `.github/` alone, and deletes `tests/test_template.py`, which tests the
   template itself.
3. Install HuRI's core and curated events, then the module, and test it:

   ```sh
   pip install "huri-core[server] @ git+https://github.com/Lucy-Robotics/huri-core.git@<ref>" \
               "huri-events @ git+https://github.com/Lucy-Robotics/huri-modules.git@<ref>#subdirectory=packages/huri-events"
   ./install.sh                            # picks requirements-{cpu,nvidia,amd}.txt for this machine
   pytest                                  # tests/ runs the module with huri_core.testing
   ```

4. Point `[project.urls]` in `pyproject.toml` at your repository.

`<ref>` is a git ref of each repository: `dev` for now, a release tag once
there is one. The two repositories have their own versions and tags
(`huri-core` 0.4.0, `huri-modules` 0.1.0, ...); pick a pair from the
compatibility table in the
[huri-modules README](https://github.com/Lucy-Robotics/huri-modules#readme).
CI does the same through `HURI_CORE_REF` and `HURI_MODULES_REF`
(`.github/workflows/ci.yml`).

## What is in it

| Path | What it is |
|---|---|
| `huri_example/module.py` | the module: a `Module` subclass with its input/output topics and `process()` |
| `huri_example/huri_module.toml` | its manifest, read by HuRI's startup check and the hub |
| `pyproject.toml` | the `huri.modules` entry point (`example = ...`; `rename.sh` renames it with everything else), the dependencies and the project URLs |
| `events/` | the events the module introduces, as their own light distribution in their own topic namespace (`example.*`) — so a client can decode them without installing the module |
| `tests/` | the module tested alone (`ModuleHarness`), and the checks the server runs at startup |
| `requirements-{cpu,nvidia,amd}.txt`, `install.sh` | hardware-specific pins, and the script choosing them |
| `.github/workflows/ci.yml` | the same, on every push, against pinned `huri-core` and `huri-modules` refs |

The concepts (modules, events, topics, manifests, the server's checks) are
described in the [huri-core README](https://github.com/Lucy-Robotics/huri-core#readme).

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

A client decoding `example.shout` installs only `events/`.

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
`huri hub search`. To be listed as verified, open a pull request to
[huri-modules](https://github.com/Lucy-Robotics/huri-modules) adding an entry to
its `registry.toml` (see its
[ACCEPTANCE.md](https://github.com/Lucy-Robotics/huri-modules/blob/main/ACCEPTANCE.md)):
a verified third-party module is pinned there as a git submodule
(`modules/<name>`) at a release tag of your repository, so tag your releases.

HuRI as a whole — what it is, how the repositories fit together — is presented
at [Lucy-Robotics/HuRI](https://github.com/Lucy-Robotics/HuRI).
