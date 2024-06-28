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
- Change directories into the repository: `cd ThermalNetwork`
- We recommend using virtual environments on principle to avoid dependencies colliding between your Python projects. [venv](https://docs.python.org/3/library/venv.html) is the Python native solution that will work everywhere, though other options may be more user-friendly.
    - Some popular alternatives are:
        - [pyenv](https://github.com/pyenv/pyenv) and [the virtualenv plugin](https://github.com/pyenv/pyenv-virtualenv) work together nicely for Linux/Mac machines
        - [virtualenv](https://virtualenv.pypa.io/en/latest/)
        - [miniconda](https://docs.conda.io/projects/miniconda/en/latest/)
        - [rye](https://rye-up.com/)

Once you have set up your environment:
- Update pip and setuptools: `pip install -U pip setuptools`
- Install the repository with developer dependencies: `pip install -e .[dev]`
- Activate pre-commit (only once, after making a new venv): `pre-commit install`
    - Runs automatically on your staged changes before every commit
    - Includes linting and formatting via [ruff](https://docs.astral.sh/ruff/)
- To check the whole repo, run `pre-commit run --all-files`
    - Settings and documentation links for pre-commit and ruff are in .pre-commit-config.yaml and pyproject.toml
    - Pre-commit will run automatically during CI, linting and formatting the entire repository.

# Testing

Once you are set up as a developer, run `pytest` from the root dir. Increase verbosity with `-v` and `-vv`.

Test coverage results will be saved to _htmlcov/index.html_.

Test files are in _tests/_

Test output will be written to _tests/test_output/_

# Releasing

Versioning is done by GitHub tag, thanks to [SetupTools-SCM](https://setuptools-scm.readthedocs.io/en/latest/). Use [semantic versioning](https://semver.org/) when tagging. When a new release is made in GitHub, a [workflow](https://github.com/marketplace/actions/pypi-publish) automatically publishes to PyPI.
