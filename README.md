
# AAPL Market Simulator

## Project Overview

This project contains an adaptive market simulator that analyzes AAPL price action to discover the trader composition and volatility structure that best explains market behavior. The simulator then uses these inferred parameters to predict future price movements.

## Features

- Loads minute-level AAPL trading data from CSV
- Runs parameter optimization to find market parameters that best explain historical price action
- Uses best-fit parameters to predict future price movements
- Evaluates prediction accuracy using Root Mean Squared Error (RMSE)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd aapl_market_simulator
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Data

The project uses `AAPL_2024.csv` containing minute-level trading data with the following columns:
- Timestamp
- Open price
- High price
- Low price
- Close price
- Volume

## Usage

1. Run the Jupyter notebook for step-by-step analysis:
   ```bash
   jupyter notebook market_simulator.ipynb
   ```

2. Or run the simulation script directly:
   ```bash
   python market_simulator.py
   ```

## Results

The simulation provides:
- Historical price analysis
- Optimized market parameters
- Price predictions with RMSE accuracy metrics
- Visualizations of trader behavior and market dynamics

## Key Performance Indicators (KPIs)

- **RMSE (Root Mean Squared Error)**: Measures prediction accuracy
- **Trader Activity Rate**: Optimized parameter for market simulation
- **Price Volatility**: Measured through moving averages and price trends
- **Order Book Imbalance**: Ratio of buy/sell orders

## Project Structure

```
aapl_market_simulator/
├── AAPL_2024.csv          # Historical price data
├── market_simulator.py    # Main simulation script
├── market_analysis.py     # Data analysis and visualization
├── market_model.py        # Market simulation models
├── requirements.txt       # Python dependencies
├── market_simulator.ipynb # Jupyter notebook with step-by-step analysis
└── README.md              # Project documentation
```

## License

This project is open source and available under the MIT License.

## Contributors

- [bchi1994](https://github.com/bchi1994) (Project author and maintainer)

