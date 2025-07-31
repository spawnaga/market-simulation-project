


"""
Test volume accounting in order book
"""

from market_model import OrderBook

def test_volume_accounting():
    """Test volume accounting"""
    print("Testing volume accounting...")

    order_book = OrderBook()

    # Place initial orders
    order_book.place_order(101, 10, True)  # Buy at 101
    print(f"After buy 101: total_buy_volume={order_book.total_buy_volume}")

    order_book.place_order(99, 15, False)  # Sell at 99
    print(f"After sell 99: total_sell_volume={order_book.total_sell_volume}")

    # This should take 5 from the sell order
    order_book.place_order(100, 5, True)  # Buy at 100 > 99
    print(f"After buy 100: total_sell_volume={order_book.total_sell_volume}")
    print(f"sell_book: {order_book.sell_book}")

    # Check if 5 was taken from the sell order
    expected_sell_volume = 15 - 5  # 15 initial - 5 taken
    assert order_book.total_sell_volume == expected_sell_volume
    assert order_book.sell_book[99] == 10  # 15 initial - 5 taken

    print("Volume accounting test passed!")

if __name__ == "__main__":
    test_volume_accounting()




