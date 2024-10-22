# ThermalNetwork

A library for sizing multiple ground heat exchangers distributed around a single-pipe thermal network.

# Installation

`pip install ThermalNetwork`

# Documentation

Available at https://nrel.github.io/ThermalNetwork/

# Usage

This package has a command-line interface, intended to be used via URBANopt. To access the CLI directly, after installing call `thermalnetwork --help` for all the commands.

# Developer installation

- Clone the repository: `git clone https://github.com/NREL/ThermalNetwork.git`
- Move into the repository: `cd ThermalNetwork`

- [Uv](https://docs.astral.sh/uv/) is used to manage the project & dependencies (and may also be used to [manage Python](https://docs.astral.sh/uv/guides/install-python/) if you want). After cloning, ensure you have
[uv installed](https://docs.astral.sh/uv/getting-started/installation/), then run `uv sync` to install the package and all development dependencies.
    - Some Windows developers have reported version conflicts using the default strategy. If this occurs, consider changing the [resolution strategy](https://docs.astral.sh/uv/concepts/resolution/#resolution-strategy) using `uv sync --resolution=lowest-direct`
- Developers can then call `uv run pytest` (which may take several minutes to run the full test suite) to confirm all dev dependencies have been
installed and everything is working as expected.
- Activate [pre-commit](https://pre-commit.com/) (only required once, after cloning the repo) with: `uv run pre-commit install`. On your first commit it will install the pre-commit environments, then run pre-commit hooks at every commit.
- Before pushing to Github, run pre-commit on all files with `uv run pre-commit run -a` to highlight any linting/formatting errors that will cause CI to fail.
- Pycharm users may need to add Ruff as a [3rd-party plugin](https://docs.astral.sh/ruff/editors/setup/#via-third-party-plugin) or install it as an [external tool](https://docs.astral.sh/ruff/editors/setup/#pycharm) to their IDE to ensure linting & formatting is consistent.
- Developers can test in-process functionality by prepending `uv run` to a terminal command. For instance, to see the CLI help menu with local changes not yet committed, run: `uv run thermalnetwork --help`

### Updating documentation
During development we can [serve docs locally](https://squidfunk.github.io/mkdocs-material/creating-your-site/#previewing-as-you-write) and view updates with every save.

   1. Start a documentation update branch: `git checkout -b <branch_name>`
   1. `uv run mkdocs serve`
   1. Point browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

# Testing

Once you are set up as a developer, run `pytest` from the root dir. Increase verbosity with `-v` and `-vv`.

Test coverage results will be saved to _htmlcov/index.html_.

Test files are in _tests/_

Test output will be written to _tests/test_output/_

# Releasing

Versioning is done by GitHub tag, thanks to [SetupTools-SCM](https://setuptools-scm.readthedocs.io/en/latest/). Use [semantic versioning](https://semver.org/) when tagging. When a new release is made in GitHub, a [workflow](https://github.com/marketplace/actions/pypi-publish) automatically publishes to PyPI.
