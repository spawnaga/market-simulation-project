

"""
Market Simulation Models
"""

import numpy as np
from scipy.optimize import minimize

class OrderBook:
    """Order book to manage buy and sell orders"""

    def __init__(self):
        self.buy_book = {}
        self.sell_book = {}
        self.last_traded_price = 0
        self.best_ask = np.inf
        self.best_bid = -np.inf
        self.trade_history = [0] * 100  # Fixed size history like in C#
        self.trade_index = 0
        self.trade_count = 0
        self.total_buy_volume = 0
        self.total_sell_volume = 0
        self.ma_5 = 3
        self.ma_25 = 3
        self.ma_50 = 3
        self.imbalance = 0
        self.trader_activity_rate = 1.0
        self.proportion_maker = 0.5
        self.price_range_percent = 0.01  # Default: 1% range (0.01 * 100%)

    def place_order(self, price, quantity, is_buy):
        """Place an order in the order book"""
        if price <= 0 or quantity <= 0:
            return

        if is_buy:  # Buy order
            if len(self.sell_book) > 0 and price > self.best_ask:
                self.take_order(price, quantity, is_buy)
            else:
                self.make_order(price, quantity, is_buy)
        else:  # Sell order
            if len(self.buy_book) > 0 and price < self.best_bid:
                self.take_order(price, quantity, is_buy)
            else:
                self.make_order(price, quantity, is_buy)

    def take_order(self, price, quantity, is_buy):
        """Execute a market order by taking existing orders"""
        remaining_quantity = quantity
        last_traded_price = self.last_traded_price

        while remaining_quantity > 0:
            if is_buy:  # Buy order taking from sell book
                if len(self.sell_book) == 0:
                    self.best_ask = np.inf
                    break
                self.best_ask = min(self.sell_book.keys())

                if price < self.best_ask:
                    break

                ask_quantity = self.sell_book[self.best_ask]
                if ask_quantity > 0:
                    trade_quantity = min(ask_quantity, remaining_quantity)
                    self.sell_book[self.best_ask] -= trade_quantity
                    remaining_quantity -= trade_quantity

                    self.total_buy_volume += trade_quantity  # Buy volume increases
                    self.total_sell_volume -= trade_quantity  # Sell volume decreases

                    last_traded_price = self.best_ask

                    if self.sell_book[self.best_ask] <= 0:
                        del self.sell_book[self.best_ask]
                        self.best_ask = min(self.sell_book.keys()) if len(self.sell_book) > 0 else np.inf
            else:  # Sell order taking from buy book
                if len(self.buy_book) == 0:
                    self.best_bid = -np.inf
                    break
                self.best_bid = max(self.buy_book.keys())

                if price < self.best_bid:
                    break

                bid_quantity = self.buy_book[self.best_bid]
                if bid_quantity > 0:
                    trade_quantity = min(bid_quantity, remaining_quantity)
                    self.buy_book[self.best_bid] -= trade_quantity
                    remaining_quantity -= trade_quantity
                    self.total_sell_volume -= trade_quantity  # Sell volume decreases
                    last_traded_price = self.best_bid

                    if self.buy_book[self.best_bid] <= 0:
                        del self.buy_book[self.best_bid]
                        self.best_bid = max(self.buy_book.keys()) if len(self.buy_book) > 0 else -np.inf

        self.last_traded_price = last_traded_price

        # Update best prices after trade
        if is_buy:  # Buy order taking from sell book
            if len(self.sell_book) == 0:
                self.best_ask = np.inf
            else:
                self.best_ask = min(self.sell_book.keys())
        else:  # Sell order taking from buy book
            if len(self.buy_book) == 0:
                self.best_bid = -np.inf
            else:
                self.best_bid = max(self.buy_book.keys())

        # Calculate imbalance
        total_volume = self.total_buy_volume + self.total_sell_volume
        if total_volume > 0:
            self.imbalance = (self.total_buy_volume - self.total_sell_volume) / total_volume
        else:
            self.imbalance = 0

        if remaining_quantity > 0:
            self.make_order(price, remaining_quantity, is_buy)

    def make_order(self, price, quantity, is_buy):
        """Add a limit order to the order book"""
        if is_buy:
            if price in self.buy_book:
                self.buy_book[price] += quantity
            else:
                self.buy_book[price] = quantity
            self.total_buy_volume += quantity
            if price > self.best_bid:
                self.best_bid = price
        else:
            if price in self.sell_book:
                self.sell_book[price] += quantity
            else:
                self.sell_book[price] = quantity
            self.total_sell_volume += quantity
            if price < self.best_ask:
                self.best_ask = price

    def record_trade(self, price):
        """Record a trade in the history"""
        self.trade_history[self.trade_index] = price
        self.trade_index = (self.trade_index + 1) % len(self.trade_history)
        self.trade_count = min(self.trade_count + 1, len(self.trade_history))

        # Update moving averages
        if self.trade_count >= 5:
            self.ma_5 = self.compute_moving_average(5)
        if self.trade_count >= 25:
            self.ma_25 = self.compute_moving_average(25)
        if self.trade_count >= 50:
            self.ma_50 = self.compute_moving_average(50)

    def compute_moving_average(self, window):
        """Compute moving average of trade history"""
        if self.trade_count < window:
            return np.mean(self.trade_history[:self.trade_count])
        return np.mean(self.trade_history[self.trade_index:self.trade_index + window] if self.trade_index + window <= len(self.trade_history)
                      else np.concatenate((self.trade_history[self.trade_index:], self.trade_history[:self.trade_index + window - len(self.trade_history)])))

    def get_chronological_trade_history(self):
        """Get trade history in chronological order"""
        chronological = [0] * len(self.trade_history)
        oldest_count = len(self.trade_history) - self.trade_index
        chronological[:oldest_count] = self.trade_history[self.trade_index:]
        chronological[oldest_count:] = self.trade_history[:self.trade_index]
        return chronological

class Trader:
    """Trader that places orders based on market conditions"""

    def __init__(self, order_book):
        self.order_book = order_book
        self.rng = np.random.RandomState()

    def try_place_orders(self):
        """Attempt to place orders with some probability"""
        if self.rng.random() < self.order_book.trader_activity_rate:
            self.place_orders()

    def place_orders(self):
        """Determine and place orders based on market conditions"""
        order = self.determine_price()
        self.order_book.place_order(order['price'], order['quantity'], order['is_buy'])

    def determine_price(self):
        """Determine order price based on market conditions (matching C# logic)"""
        last_price = self.order_book.last_traded_price
        short_ma = self.order_book.ma_5
        long_ma = self.order_book.ma_25

        short_trend = (last_price - short_ma) / short_ma if short_ma != 0 else 0
        long_trend = (last_price - long_ma) / long_ma if long_ma != 0 else 0

        is_maker = self.rng.random() < self.order_book.proportion_maker

        # Make price range percentage a parameter (0.01% to 3.00%)
        price_range_percent = self.order_book.price_range_percent
        rand_factor = 1.0 + (self.rng.random() * price_range_percent - price_range_percent / 2)
        rand_price = int(last_price * rand_factor + 0.5 * np.sign(rand_factor - 1))

        if is_maker:
            if rand_price > last_price:
                # Maker selling (higher price)
                return {'price': rand_price, 'quantity': self.rng.randint(1, 41), 'is_buy': False}
            else:
                # Maker buying (lower price)
                return {'price': rand_price, 'quantity': self.rng.randint(1, 41), 'is_buy': True}
        else:
            # Taker logic: buy high, sell low (inefficient)
            if rand_price > last_price:
                # Taker buying high (inefficient)
                return {'price': rand_price, 'quantity': self.rng.randint(1, 21), 'is_buy': True}
            else:
                # Taker selling low (inefficient)
                return {'price': rand_price, 'quantity': self.rng.randint(1, 21), 'is_buy': False}

class MarketSimulator:
    """Market simulator that runs the simulation and optimizes parameters"""

    def __init__(self, order_book, traders):
        self.order_book = order_book
        self.traders = traders
        self.initial_params = {
            'trader_activity_rate': 1.0,
            'proportion_maker': 0.5
        }

    def optimize_parameters(self, df):
        """Optimize market parameters to best explain historical data"""
        initial_params = [self.initial_params['trader_activity_rate'],
                         self.initial_params['proportion_maker']]

        result = minimize(self._objective_function, initial_params,
                         args=(df), bounds=[(0.1, 2.0), (0.1, 0.9)],
                         method='L-BFGS-B')

        optimized_params = {
            'trader_activity_rate': result.x[0],
            'proportion_maker': result.x[1]
        }

        return optimized_params

    def _objective_function(self, params, df):
        """Objective function for parameter optimization"""
        # Create a temporary order book for this evaluation
        temp_order_book = OrderBook()
        temp_order_book.trader_activity_rate = params[0]
        temp_order_book.proportion_maker = params[1]

        # Create temporary traders
        temp_traders = [Trader(temp_order_book) for _ in range(len(self.traders))]

        # Create temporary simulator
        temp_simulator = MarketSimulator(temp_order_book, temp_traders)

        # Run a short simulation to evaluate parameters
        predictions = temp_simulator.run_simulation(df, {
            'trader_activity_rate': params[0],
            'proportion_maker': params[1]
        })
        actual = df['close'].values
        error = np.sqrt(np.mean((actual - predictions) ** 2))
        return error

    def run_simulation(self, df, params):
        """Run market simulation with given parameters"""
        self.order_book.trader_activity_rate = params['trader_activity_rate']
        self.order_book.proportion_maker = params['proportion_maker']
        self.order_book.price_range_percent = params.get('price_range_percent', 0.01)

        predictions = []
        current_price = df['open'].iloc[0]
        self.order_book.last_traded_price = current_price

        for i in range(len(df)):
            # Process market for each time step
            for trader in self.traders:
                trader.try_place_orders()

            # Calculate simulated price based on order book dynamics
            if len(self.order_book.buy_book) > 0 and len(self.order_book.sell_book) > 0:
                # Use order book imbalance to determine price movement
                if self.order_book.imbalance > 0:
                    # More buy volume - price should increase
                    price_change = (self.order_book.best_bid - current_price) * 0.1
                else:
                    # More sell volume - price should decrease
                    price_change = (self.order_book.best_ask - current_price) * 0.1

                # Add some randomness to simulate market noise
                price_change += np.random.normal(0, 0.01 * current_price)

                # Update price while keeping it reasonable
                new_price = current_price + price_change
                new_price = max(new_price, 0.95 * current_price)  # Don't let it drop too fast
                new_price = min(new_price, 1.05 * current_price)  # Don't let it rise too fast

                current_price = new_price
            else:
                # If no orders, use a small random walk
                current_price += np.random.normal(0, 0.005 * current_price)

            # Record the trade
            self.order_book.record_trade(int(current_price))
            self.order_book.last_traded_price = int(current_price)
            predictions.append(current_price)

        return np.array(predictions)

    def run_multiple_simulations(self, df, window_size=30, prediction_size=5, num_simulations=1000):
        """
        Run multiple simulations to find best parameters and make predictions

        Args:
            df: DataFrame with historical data
            window_size: Number of minutes to use for parameter optimization
            prediction_size: Number of minutes to predict
            num_simulations: Number of parameter combinations to test

        Returns:
            List of RMSE values for each prediction window
        """
        rmse_results = []
        current_index = window_size  # Start with enough data for initial optimization

        # Generate parameter grid
        activity_rates = np.linspace(0.2, 2.0, num_simulations)
        maker_proportions = np.linspace(0.1, 0.9, num_simulations)
        price_ranges = np.linspace(0.0001, 0.03, num_simulations)  # 0.01% to 3.00%

        while current_index + prediction_size <= len(df):
            # Extract current window for optimization (look back window_size minutes)
            optimization_window = df.iloc[current_index - window_size:current_index]

            best_rmse = float('inf')
            best_params = None

            # Test different parameter combinations
            for i in range(num_simulations):
                params = {
                    'trader_activity_rate': activity_rates[i],
                    'proportion_maker': maker_proportions[i],
                    'price_range_percent': price_ranges[i]
                }

                # Run simulation with these parameters
                predictions = self.run_simulation(optimization_window, params)
                actual = optimization_window['close'].values
                rmse = np.sqrt(np.mean((actual - predictions) ** 2))

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_params = params

            # Store the best RMSE for this window
            rmse_results.append(best_rmse)

            # Use best parameters to predict next window
            prediction_window = df.iloc[current_index:current_index + prediction_size]
            prediction = self.run_simulation(prediction_window, best_params)

            # Compare to actual data
            actual_next_window = df.iloc[current_index:current_index + prediction_size]['close'].values
            prediction_rmse = np.sqrt(np.mean((actual_next_window - prediction) ** 2))
            rmse_results.append(prediction_rmse)

            # Move to next window (sliding window approach)
            current_index += prediction_size

        return rmse_results


