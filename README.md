
# Mesa Trade Sim (starter)

A minimal, git-ready starter for a two-goods trade & information-flow simulation using [Mesa](https://mesa.readthedocs.io/) and NetworkX.

**Note:** Mesa's visualization components rely on Solara, which currently supports Python versions up to 3.12.

## Quick start (pip + venv)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt  # installs Mesa with Solara extras
python -m sim.run --steps 50 --agents 50 --p_edge 0.1
```

## Optional: Poetry
```bash
poetry install
poetry run python -m sim.run --steps 50 --agents 50 --p_edge 0.1
```

## Run with visualization (optional)
```bash
solara run sim/viz.py -- --agents 50 --p_edge 0.1  # launches Solara viz (Python ≤3.12)
```
Note: `solara run` is required because `solara.run` is deprecated.

## Project layout
```
src/
  sim/
    __init__.py
    model.py
    run.py
    viz.py
requirements.txt
pyproject.toml  (optional Poetry)
.gitignore
```

## Notes
- `run.py` runs a headless simulation and prints a small summary.
- `viz.py` launches a Solara-based network visualization, handy for debugging.
- This is intentionally small; extend agent rules, add price formation, and write events to Parquet/DuckDB as you go.
