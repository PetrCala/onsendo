<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-top: 20px; margin-bottom: 20px;">
  <h1 style="color: #d2691e; font-size: 2.5em; font-weight: bold; margin-bottom: 0px;">温泉道️</h1>
  <h5 style="margin-bottom: 20px; font-weight: normal;">♨️ 大なる温泉の道 ♨️</h5>
  <p style="font-weight: normal;">
    This is a Python-based application to help me manage and track onsen (hot spring) visits and experiences, while in Beppu. It provides a command-line interface for adding onsen locations, recording visits with personal ratings, and managing the onsen journey data.
  </p>
  <p>
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
    </a>
    <a href="https://www.sqlite.org/index.html">
      <img src="https://img.shields.io/badge/sqlite-3-blue.svg" alt="SQLite 3">
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
    </a>
  </p>
</div>

- [Set up the project](#set-up-the-project)
- [How to use](#how-to-use)
  - [Preparing a database](#preparing-a-database)
  - [Using Command Line Interface](#using-command-line-interface)

## Set up the project

- Get [Python](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/docs/)
- Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

- Run `poetry install`

## How to use

### Preparing a database

You can either choose to create your own database, or use the provided one.

- To create a new database, run `poetry run python scripts/init_db.py`. This creates a new sub-folder in the `data` folder, and puts a new SQLite database file there.
- To use the provided database, simply copy it over to this folder.

<!-- TODO this should be clearer -->

### Using Command Line Interface

The project offers a number of utility functions through a simple CLI. To list these, run the following:

```bash
poetry run onsendo --help
```
