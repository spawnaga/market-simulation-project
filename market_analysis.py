

"""
Market Analysis and Visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error

def analyze_data(df):
    """Perform initial data analysis"""
    results = {}

    # Basic statistics
    results['mean_price'] = df['close'].mean()
    results['std_price'] = df['close'].std()
    results['price_range'] = df['close'].max() - df['close'].min()

    # Moving averages
    results['ma_5'] = df['close'].rolling(window=5).mean().iloc[-1]
    results['ma_25'] = df['close'].rolling(window=25).mean().iloc[-1]
    results['ma_50'] = df['close'].rolling(window=50).mean().iloc[-1]

    # Volatility
    results['price_volatility'] = df['close'].pct_change().std()

    # Volume analysis
    results['mean_volume'] = df['volume'].mean()
    results['max_volume'] = df['volume'].max()

    # Plot price trends
    plt.figure(figsize=(12, 6))
    plt.plot(df['close'], label='Close Price')
    plt.plot(df['close'].rolling(window=5).mean(), label='5-period MA')
    plt.plot(df['close'].rolling(window=25).mean(), label='25-period MA')
    plt.title('AAPL Price Trends')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.savefig('price_trends.png')
    plt.close()

    # Plot volume trends
    plt.figure(figsize=(12, 4))
    plt.plot(df['volume'], label='Volume', color='green')
    plt.title('AAPL Trading Volume')
    plt.xlabel('Time')
    plt.ylabel('Volume')
    plt.savefig('volume_trends.png')
    plt.close()

    return results

def evaluate_predictions(actual, predicted):
    """Evaluate prediction accuracy"""
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    return rmse

def plot_simulation_results(actual, predicted):
    """Plot simulation results"""
    plt.figure(figsize=(12, 6))
    plt.plot(actual, label='Actual Price', color='blue')
    plt.plot(predicted, label='Predicted Price', color='red', linestyle='--')
    plt.title('Market Simulation Results')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.savefig('simulation_results.png')
    plt.close()

    # Plot error distribution
    errors = actual - predicted
    plt.figure(figsize=(10, 5))
    sns.histplot(errors, kde=True)
    plt.title('Error Distribution')
    plt.xlabel('Prediction Error')
    plt.savefig('error_distribution.png')
    plt.close()

    return errors


