"""Solara-based visualization for the TradeModel."""

import argparse

import solara as sl
from mesa.visualization import SolaraViz
from solara.server import app as solara_app

from sim.model import TradeModel


def build_app(agents: int = 50, p_edge: float = 0.1):
    """Create a Solara page hosting the Mesa visualization."""

    @sl.component
    def Page():
        viz = SolaraViz(
            model_cls=TradeModel,
            model_params={"N": agents, "p_edge": p_edge},
            measures=[
                ("avg_capital", "Average Capital"),
                ("trade_volume", "Trades per Tick"),
            ],
        )
        viz.render()

    return Page


# Default app so "solara run sim/viz.py" works out of the box
app = build_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Launch Solara visualization for the TradeModel"
    )
    parser.add_argument("--agents", type=int, default=50, help="Number of agents")
    parser.add_argument("--p_edge", type=float, default=0.1, help="Edge probability")
    args = parser.parse_args()

    solara_app.AppScript(build_app(args.agents, args.p_edge)).run()

