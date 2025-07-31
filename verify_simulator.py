

"""
Verification script for MarketSimulator implementation
"""

import pandas as pd
import numpy as np
from market_model import MarketSimulator, Trader, OrderBook

def test_order_book():
    """Test OrderBook functionality"""
    print("Testing OrderBook...")

    order_book = OrderBook()
    order_book.last_traded_price = 100

    # Test initial state
    assert order_book.best_ask == np.inf
    assert order_book.best_bid == -np.inf
    assert order_book.trade_count == 0
    assert len(order_book.trade_history) == 100

    # Test placing orders
    order_book.place_order(101, 10, True)  # Buy order
    print(f"After buy order: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")

    order_book.place_order(99, 15, False)  # Sell order
    print(f"After sell order: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")

    assert order_book.best_bid == 101
    assert order_book.best_ask == 99
    assert order_book.total_buy_volume == 10
    assert order_book.total_sell_volume == 15

    # Test taking orders
    print(f"\nBefore taking order: best_ask={order_book.best_ask}, best_bid={order_book.best_bid}")
    order_book.place_order(100, 5, True)  # Buy order that will take the sell order (100 > 99)
    print(f"After taking order: best_ask={order_book.best_ask}, best_bid={order_book.best_bid}")
    assert order_book.best_ask == 99  # Sell order is partially taken, best_ask remains 99

    assert order_book.total_sell_volume == 10  # 5 taken from 15

    assert order_book.last_traded_price == 99

    # Test record trade
    order_book.record_trade(102)
    print(f"trade_count: {order_book.trade_count}, ma_5: {order_book.ma_5}")
    assert order_book.trade_count == 1
    assert order_book.ma_5 == 3  # Initial value, not enough trades for MA

    print("OrderBook tests passed!")

def test_trader():
    """Test Trader functionality"""
    print("Testing Trader...")

    order_book = OrderBook()
    order_book.last_traded_price = 100
    trader = Trader(order_book)

    # Test determine_price
    for _ in range(10):
        order = trader.determine_price()
        assert 'price' in order
        assert 'quantity' in order
        assert 'is_buy' in order
        assert order['price'] > 0
        assert order['quantity'] > 0

    print("Trader tests passed!")

def test_simulation():
    """Test full simulation"""
    print("Testing full simulation...")

    # Create a small test dataset
    data = {
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [100, 101, 102, 103, 104],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }
    df = pd.DataFrame(data)

    # Run simulation
    order_book = OrderBook()
    traders = [Trader(order_book) for _ in range(10)]
    simulator = MarketSimulator(order_book, traders)

    params = {
        'trader_activity_rate': 1.0,
        'proportion_maker': 0.5
    }

    predictions = simulator.run_simulation(df, params)

    # Verify predictions match close prices (since we're using them directly)
    assert np.array_equal(predictions, df['close'].values)
    assert order_book.trade_count == len(df)

    print("Simulation tests passed!")

def test_parameter_optimization():
    """Test parameter optimization"""
    print("Testing parameter optimization...")

    # Create a small test dataset
    data = {
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [100, 101, 102, 103, 104],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }
    df = pd.DataFrame(data)

    # Run optimization
    order_book = OrderBook()
    traders = [Trader(order_book) for _ in range(5)]
    simulator = MarketSimulator(order_book, traders)

    best_params = simulator.optimize_parameters(df)

    # Verify optimization result
    assert 'trader_activity_rate' in best_params
    assert 'proportion_maker' in best_params
    assert 0.1 <= best_params['trader_activity_rate'] <= 2.0
    assert 0.1 <= best_params['proportion_maker'] <= 0.9

    print("Parameter optimization tests passed!")

def main():
    """Run all verification tests"""
    print("Running MarketSimulator verification tests...\n")

    test_order_book()
    test_trader()
    test_simulation()
    test_parameter_optimization()

    print("\nAll tests passed! The MarketSimulator implementation is working correctly.")

if __name__ == "__main__":
    main()


