

"""
Realistic Market Simulator for AAPL
"""

import pandas as pd
import numpy as np
from market_model import MarketSimulator, Trader, OrderBook
from market_analysis import analyze_data, evaluate_predictions

def load_data(filepath):
    """Load AAPL trading data from CSV"""
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'open', 'high', 'low', 'close', 'volume'],
                    parse_dates=['timestamp'])
    return df

def main():
    # Load data
    print("Loading AAPL trading data...")
    df = load_data('AAPL_2024.csv')

    # Perform initial analysis
    print("\nPerforming data analysis...")
    analysis_results = analyze_data(df)

    # Initialize market simulator
    print("\nInitializing market simulator...")
    order_book = OrderBook()
    traders = [Trader(order_book) for _ in range(50)]  # Create 50 traders
    simulator = MarketSimulator(order_book, traders)

    # Run parameter optimization
    print("Running parameter optimization...")
    best_params = simulator.optimize_parameters(df)

    # Run simulation with best parameters
    print("Running market simulation...")
    predictions = simulator.run_simulation(df, best_params)

    # Evaluate results
    print("\nEvaluating simulation results...")
    rmse = evaluate_predictions(df['close'].values, predictions)
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")

    # Save results
    results_df = pd.DataFrame({
        'timestamp': df['timestamp'],
        'actual': df['close'].values,
        'predicted': predictions
    })
    results_df.to_csv('simulation_results_realistic.csv', index=False)
    print("Results saved to simulation_results_realistic.csv")

if __name__ == "__main__":
    main()


