import datetime
import random
from typing import List, Tuple
from orb_logic import ORBEngine, Direction


def generate_synthetic_ticks(
    symbol: str,
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    base_price: float,
    volatility: float = 0.01,
    trend: float = 0.0005
) -> List[Tuple[datetime.datetime, float]]:
    """
    Generate synthetic price ticks for testing.

    Args:
        symbol: Stock symbol
        start_time: Start timestamp
        end_time: End timestamp
        base_price: Starting price
        volatility: Price volatility (standard deviation of price changes)
        trend: Price trend (drift per tick)

    Returns:
        List of (timestamp, price) tuples
    """
    ticks = []
    current_time = start_time
    current_price = base_price

    while current_time <= end_time:
        # Generate price change with some randomness
        price_change = random.gauss(trend, volatility)
        current_price += price_change

        # Ensure price stays positive
        current_price = max(current_price, 0.01)

        ticks.append((current_time, current_price))

        # Increment time by 1 minute (for 1-minute candle data)
        current_time += datetime.timedelta(minutes=1)

    return ticks


def create_breakout_scenario(
    symbol: str = "RELIANCE",
    base_price: float = 2400.0
) -> Tuple[List[Tuple[datetime.datetime, float]], dict]:
    """
    Create a synthetic scenario that will produce a clear bullish breakout.

    Returns:
        Tuple of (ticks list, expected_range_info)
    """
    # Define the trading session (9:15 AM to 10:00 AM)
    today = datetime.datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
    start_time = today
    end_time = today.replace(hour=10, minute=0, second=0, microsecond=0)

    # Generate ticks with a clear breakout after 9:30 AM
    ticks = []
    current_time = start_time
    current_price = base_price

    # First 15 minutes (9:15-9:30): Establish a tight range
    range_high = base_price * 1.005  # 0.5% above base
    range_low = base_price * 0.995   # 0.5% below base

    while current_time <= today.replace(hour=9, minute=30, second=0, microsecond=0):
        # Oscillate within the range
        price = base_price + random.uniform(-0.005, 0.005) * base_price
        ticks.append((current_time, price))
        current_time += datetime.timedelta(minutes=1)

    # After 9:30 AM: Create a clear bullish breakout
    breakout_time = today.replace(hour=9, minute=31, second=0, microsecond=0)
    while current_time <= end_time:
        if current_time < breakout_time:
            # Just before breakout, stay in range
            price = base_price + random.uniform(-0.003, 0.003) * base_price
        else:
            # After breakout time, price rises sharply
            breakout_progress = (current_time - breakout_time).total_seconds() / 300  # 5 minutes to peak
            breakout_boost = min(0.02, breakout_progress * 0.004)  # Up to 2% boost
            price = base_price * (1 + 0.005 + breakout_boost)  # Above range high

        ticks.append((current_time, price))
        current_time += datetime.timedelta(minutes=1)

    # Calculate expected range
    expected_high = base_price * 1.005
    expected_low = base_price * 0.995
    expected_midpoint = (expected_high + expected_low) / 2

    expected_range_info = {
        "symbol": symbol,
        "opening_range_high": expected_high,
        "opening_range_low": expected_low,
        "range_midpoint": expected_midpoint,
        "is_range_locked": True
    }

    return ticks, expected_range_info


def test_orb_with_synthetic_data():
    """Test the ORB engine with synthetic data that should produce a breakout."""
    symbol = "RELIANCE"
    ticks, expected_range = create_breakout_scenario(symbol)

    # Create ORB engine
    orb = ORBEngine(symbol)

    # Process all ticks
    breakout_detected = False
    breakout_info = None

    for timestamp, price in ticks:
        # Add tick to engine (this updates the range)
        orb.add_tick(timestamp, price)

        # After adding the tick, check for breakout
        if orb.is_range_locked:  # Only check after range is locked
            result = orb.check_breakout(timestamp, price)
            if result:
                breakout_detected = True
                direction, entry_price, stop_loss, target = result
                breakout_info = {
                    "direction": direction.value,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "target": target,
                    "timestamp": timestamp
                }
                break  # Stop at first breakout for this test

    return {
        "breakout_detected": breakout_detected,
        "breakout_info": breakout_info,
        "final_range": orb.get_range_info(),
        "expected_range": expected_range,
        "total_ticks": len(ticks)
    }


if __name__ == "__main__":
    # Run the test when script is executed directly
    result = test_orb_with_synthetic_data()
    print("ORB Engine Test Results:")
    print(f"Breakout detected: {result['breakout_detected']}")
    if result['breakout_info']:
        info = result['breakout_info']
        print(f"Direction: {info['direction']}")
        print(f"Entry Price: {info['entry_price']:.2f}")
        print(f"Stop Loss: {info['stop_loss']:.2f}")
        print(f"Target: {info['target']:.2f}")
        print(f"Breakout Time: {info['timestamp']}")
    print(f"Final Range: {result['final_range']}")
    print(f"Expected Range: {result['expected_range']}")
    print(f"Total Ticks Processed: {result['total_ticks']}")