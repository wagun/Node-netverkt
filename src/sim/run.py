
import argparse
from sim.model import TradeModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--agents", type=int, default=50)
    parser.add_argument("--p_edge", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    model = TradeModel(N=args.agents, p_edge=args.p_edge, seed=args.seed)
    for _ in range(args.steps):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    print(df.tail())
    print("\nSummary:")
    print(f"Steps: {args.steps}, Agents: {args.agents}, p_edge: {args.p_edge}")
    print(f"Avg capital final: {df['avg_capital'].iloc[-1]:.2f}")
    print(f"Trade volume last tick: {df['trade_volume'].iloc[-1]}")
    print(f"Gini (capital) last tick: {df['gini_capital'].iloc[-1]:.3f}")

if __name__ == "__main__":
    main()
