

"""
Filtered Market Simulation - Runs simulation during regular trading hours only
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from market_model import MarketSimulator, Trader, OrderBook
from market_analysis import analyze_data, evaluate_predictions

def load_and_filter_data(filepath):
    """Load AAPL trading data from CSV and filter for regular trading hours"""
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'open', 'high', 'low', 'close', 'volume'],
                    parse_dates=['timestamp'])

    # Filter for regular trading hours (10:01 AM to 3:55 PM)
    df = df[df['timestamp'].dt.time >= pd.Timestamp('10:01').time()]
    df = df[df['timestamp'].dt.time <= pd.Timestamp('15:55').time()]

    return df

def main():
    # Load and filter data
    print("Loading and filtering AAPL trading data...")
    df = load_and_filter_data('AAPL_2024.csv')

    # Check if we have enough data for the simulation
    if len(df) < 100:
        print("Error: Not enough data after filtering. Please check the data file.")
        return

    # Perform initial analysis
    print("\nPerforming data analysis...")
    analysis_results = analyze_data(df)

    # Initialize market simulator
    print("\nInitializing market simulator...")
    order_book = OrderBook()
    traders = [Trader(order_book) for _ in range(50)]  # Create 50 traders
    simulator = MarketSimulator(order_book, traders)

    # Run enhanced simulation with multiple windows
    print("Running enhanced simulation with multiple windows...")
    window_size = 30  # 30 minutes for parameter optimization
    prediction_size = 5  # 5 minutes for prediction
    num_simulations = 10  # Test 10 parameter combinations (for quick test)

    rmse_results = simulator.run_multiple_simulations(df, window_size, prediction_size, num_simulations)

    # Evaluate results
    print("\nEvaluating simulation results...")
    optimization_rmse = rmse_results[::2]  # RMSE for optimization windows
    prediction_rmse = rmse_results[1::2]   # RMSE for prediction windows

    print(f"Average optimization window RMSE: {np.mean(optimization_rmse):.4f}")
    print(f"Average prediction window RMSE: {np.mean(prediction_rmse):.4f}")
    print(f"Total prediction windows: {len(prediction_rmse)}")

    # Save results
    results_df = pd.DataFrame({
        'optimization_rmse': optimization_rmse,
        'prediction_rmse': prediction_rmse
    })
    results_df.to_csv('simulation_results_filtered.csv', index=False)
    print("Results saved to simulation_results_filtered.csv")

    # Plot RMSE over time
    plt.figure(figsize=(12, 6))
    plt.plot(optimization_rmse, label='Optimization Window RMSE', alpha=0.7)
    plt.plot(prediction_rmse, label='Prediction Window RMSE', alpha=0.7)
    plt.title('RMSE Over Time (Filtered Trading Hours)')
    plt.xlabel('Time Window')
    plt.ylabel('RMSE')
    plt.legend()
    plt.savefig('rmse_over_time_filtered.png')
    plt.close()

    print("RMSE visualization saved to rmse_over_time_filtered.png")

if __name__ == "__main__":
    main()

