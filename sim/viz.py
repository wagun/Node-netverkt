
from mesa.visualization.modules import NetworkModule, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
import networkx as nx
from sim.model import TradeModel

def network_portrayal(G):
    def node_color(agent):
        return "#1f77b4" if agent.specialty == "wheat" else "#ff7f0e"

    portrayal = {"nodes": [], "edges": []}
    for (a, b) in G.edges:
        portrayal["edges"].append({"source": a, "target": b, "color": "#cccccc"})
    for node_id in G.nodes:
        agents = G.nodes[node_id].get("agent", [])
        color = "#888888"
        if agents:
            color = node_color(agents[0])
        portrayal["nodes"].append({"id": node_id, "size": 6, "color": color})
    return portrayal

def launch(agents=50, p_edge=0.1):
    # Note: NetworkModule expects a function that maps G->portrayal
    network = NetworkModule(network_portrayal, 800, 600)
    chart = ChartModule(
        [{"Label": "avg_capital", "Color": "black"},
         {"Label": "trade_volume", "Color": "green"}],
        data_collector_name="datacollector",
    )
    model_params = {
        "N": UserSettableParameter("slider", "Agents", agents, 10, 300, 10),
        "p_edge": UserSettableParameter("slider", "Edge Prob", p_edge, 0.01, 0.5, 0.01),
    }
    server = ModularServer(TradeModel, [network, chart], "Two-Goods Trade", model_params)
    server.port = 8521
    server.launch()

if __name__ == "__main__":
    launch()
