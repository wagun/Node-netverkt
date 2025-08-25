
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple
import random

import networkx as nx

try:  # pragma: no cover - import failure is a runtime concern
    from mesa import Agent, Model
    from mesa.space import NetworkGrid
    from mesa.datacollection import DataCollector
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Mesa is required to run this simulation. Install it with"
        " 'pip install -r requirements.txt'."
    ) from exc


Goods = Tuple[str, str]  # e.g., ('wheat', 'iron')


@dataclass
class Offer:
    good: str
    qty: int
    price: float  # price per unit (numeraire)


class Trader(Agent):
    def __init__(self, model: "TradeModel", specialty: str):
        super().__init__(model)
        self.specialty = specialty  # the good this agent produces cheaper
        self.capital: float = 100.0
        self.inventory: Dict[str, int] = {g: 0 for g in model.goods}
        # Initial endowment: specialize in one good
        self.inventory[self.specialty] = 10

    def production(self) -> None:
        # Simple production: more efficient at specialty
        base = 1
        bonus = 2 if self.specialty else 0
        self.inventory[self.specialty] += base + bonus

    def quote_price(self, good: str) -> float:
        # Naive pricing: specialty cheaper to sell, others expensive
        base = 5.0
        if good == self.specialty:
            return base * 0.8
        return base * 1.3

    def step(self) -> None:
        # 1) produce
        self.production()

        # 2) pick a neighbor to trade with
        neighbors = self.model.grid.get_neighbors(self.pos, include_center=False)
        if not neighbors:
            return
        partner = random.choice(neighbors)

        # 3) choose desired good (not your specialty) and attempt trade
        wants = [g for g in self.model.goods if g != self.specialty]
        if not wants:
            return
        my_price = self.quote_price(self.specialty)
        their_price = partner.quote_price(partner.specialty)

        # Simple bilateral trade: 1 unit each direction if both have stock and can afford
        if self.inventory[self.specialty] > 0 and partner.inventory[partner.specialty] > 0:
            # compute trade values
            my_out = my_price
            their_out = their_price

            if partner.capital >= my_out and self.capital >= their_out:
                # execute trades
                self.inventory[self.specialty] -= 1
                partner.inventory[self.specialty] += 1
                partner.capital -= my_out
                self.capital += my_out

                partner.inventory[partner.specialty] -= 1
                self.inventory[partner.specialty] += 1
                self.capital -= their_out
                partner.capital += their_out

                # record
                self.model.trades_this_tick += 1

class TradeModel(Model):
    def __init__(self, N: int, p_edge: float, goods: Goods = ("wheat", "iron"), seed: int | None = None):
        super().__init__()
        if seed is not None:
            random.seed(seed)
            self._seed = seed
        self.goods = goods
        self.G = nx.erdos_renyi_graph(N, p_edge, seed=seed)
        self.grid = NetworkGrid(self.G)
        self.trades_this_tick = 0

        # create agents, half specialize in good0, half in good1
        for i in range(N):
            specialty = goods[i % len(goods)]
            a = Trader(self, specialty=specialty)
            self.grid.place_agent(a, i)

        self.datacollector = DataCollector(
            model_reporters={
                "avg_capital": lambda m: sum(a.capital for a in m.agents) / len(m.agents),
                "trade_volume": lambda m: m.trades_this_tick,
                "gini_capital": self._gini_capital,
            }
        )

    def _gini_capital(self) -> float:
        vals = sorted([a.capital for a in self.agents])
        n = len(vals)
        if n == 0:
            return 0.0
        cum = 0.0
        for i, x in enumerate(vals, start=1):
            cum += i * x
        return (2 * cum) / (n * sum(vals)) - (n + 1) / n

    def step(self) -> None:
        self.trades_this_tick = 0
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
