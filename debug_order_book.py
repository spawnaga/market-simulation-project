

"""
Debug OrderBook functionality
"""

from market_model import OrderBook

def debug_order_book():
    """Debug OrderBook functionality"""
    print("Debugging OrderBook...")

    order_book = OrderBook()
    order_book.last_traded_price = 100

    print(f"Initial state: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")

    # Test placing orders
    print("\nPlacing buy order (101, 10):")
    order_book.place_order(101, 10, True)
    print(f"After buy order: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")
    print(f"Buy book: {order_book.buy_book}")
    print(f"Sell book: {order_book.sell_book}")
    print(f"total_buy_volume: {order_book.total_buy_volume}, total_sell_volume: {order_book.total_sell_volume}")
    print(f"Assertion check: best_bid == 101? {order_book.best_bid == 101}")

    print("\nPlacing sell order (99, 15):")
    order_book.place_order(99, 15, False)
    print(f"After sell order: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")
    print(f"Buy book: {order_book.buy_book}")
    print(f"Sell book: {order_book.sell_book}")

    print("\nPlacing buy order (100, 5) that should take the sell order:")
    order_book.place_order(100, 5, True)
    print(f"After taking order: best_bid={order_book.best_bid}, best_ask={order_book.best_ask}")
    print(f"Buy book: {order_book.buy_book}")
    print(f"Sell book: {order_book.sell_book}")
    print(f"Last traded price: {order_book.last_traded_price}")

if __name__ == "__main__":
    debug_order_book()


