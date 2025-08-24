
# Mesa Trade Sim (starter)

A minimal, git-ready starter for a two-goods trade & information-flow simulation using [Mesa](https://mesa.readthedocs.io/) and NetworkX.

## Quick start (pip + venv)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
python -m sim.run --steps 50 --agents 50 --p_edge 0.1
```

## Optional: Poetry
```bash
poetry install
poetry run python -m sim.run --steps 50 --agents 50 --p_edge 0.1
```

## Run with visualization (optional)
```bash
python -m sim.viz --agents 50 --p_edge 0.1
```

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
- `viz.py` launches Mesa's web server with a simple network visualization, handy for debugging.
- This is intentionally small; extend agent rules, add price formation, and write events to Parquet/DuckDB as you go.
