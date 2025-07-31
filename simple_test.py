


"""
Simple test for order book logic
"""

from market_model import OrderBook

def simple_test():
    """Simple test of order book functionality"""
    print("Running simple order book test...")

    order_book = OrderBook()

    # Place initial orders
    order_book.place_order(101, 10, True)  # Buy at 101
    print(f"After buy 101: best_bid={order_book.best_bid}, sell_book={order_book.sell_book}")

    order_book.place_order(99, 15, False)  # Sell at 99
    print(f"After sell 99: best_ask={order_book.best_ask}, sell_book={order_book.sell_book}")

    # This should take the sell order
    order_book.place_order(100, 5, True)  # Buy at 100 > 99
    print(f"After buy 100: best_ask={order_book.best_ask}, sell_book={order_book.sell_book}")
    print(f"total_sell_volume: {order_book.total_sell_volume}")

    # Check if sell book is empty
    print(f"sell_book empty: {len(order_book.sell_book) == 0}")

if __name__ == "__main__":
    simple_test()



