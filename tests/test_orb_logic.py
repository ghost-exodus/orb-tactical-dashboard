import unittest
import datetime
import random
from orb_logic import ORBEngine, Direction


class TestORBLogic(unittest.TestCase):
    """Unit tests for the ORB logic engine."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.symbol = "TEST"
        self.orb = ORBEngine(self.symbol)
        self.base_time = datetime.datetime(2026, 6, 16, 9, 15, 0)  # 9:15 AM

    def test_initial_state(self):
        """Test initial state of ORB engine."""
        self.assertFalse(self.orb.is_range_locked)
        self.assertIsNone(self.orb.opening_range_high)
        self.assertIsNone(self.orb.opening_range_low)
        self.assertIsNone(self.orb.range_midpoint)
        self.assertEqual(len(self.orb.ticks), 0)

    def test_add_ticks_during_opening_range(self):
        """Test adding ticks during the opening range period (9:15-9:30)."""
        # Add ticks within the opening range
        for i in range(15):  # 15 minutes of data
            timestamp = self.base_time + datetime.timedelta(minutes=i)
            price = 100.0 + i * 0.1  # Gradually increasing price
            self.orb.add_tick(timestamp, price)

        # Range should not be locked yet
        self.assertFalse(self.orb.is_range_locked)
        self.assertEqual(self.orb.opening_range_low, 100.0)  # First price
        self.assertEqual(self.orb.opening_range_high, 101.4)  # Last price (100 + 14*0.1)
        self.assertIsNone(self.orb.range_midpoint)

    def test_range_locked_after_930(self):
        """Test that range locks after 9:30 AM."""
        # Add ticks during opening range (9:15-9:30)
        for i in range(15):
            timestamp = self.base_time + datetime.timedelta(minutes=i)
            price = 100.0 + random.uniform(-0.5, 0.5)
            self.orb.add_tick(timestamp, price)

        # Add one tick after 9:30 AM
        timestamp_after = self.base_time + datetime.timedelta(minutes=16)  # 9:31 AM
        self.orb.add_tick(timestamp_after, 102.0)

        # Range should now be locked
        self.assertTrue(self.orb.is_range_locked)
        self.assertIsNotNone(self.orb.opening_range_high)
        self.assertIsNotNone(self.orb.opening_range_low)
        self.assertIsNotNone(self.orb.range_midpoint)

        # Midpoint should be average of high and low
        expected_midpoint = (self.orb.opening_range_high + self.orb.opening_range_low) / 2
        self.assertAlmostEqual(self.orb.range_midpoint, expected_midpoint, places=2)

    def test_bullish_breakout_detection(self):
        """Test detection of bullish breakout."""
        # Establish opening range (9:15-9:30)
        base_price = 100.0
        for i in range(15):
            timestamp = self.base_time + datetime.timedelta(minutes=i)
            # Oscillate between 99.5 and 100.5
            price = base_price + ((-1) ** i) * 0.5
            self.orb.add_tick(timestamp, price)

        # Lock the range by adding a tick after 9:30 AM
        self.orb.add_tick(self.base_time + datetime.timedelta(minutes=16), 100.0)

        # Verify range is established
        self.assertAlmostEqual(self.orb.opening_range_low, 99.5, places=1)
        self.assertAlmostEqual(self.orb.opening_range_high, 100.5, places=1)
        self.assertAlmostEqual(self.orb.range_midpoint, 100.0, places=1)

        # Now simulate a bullish breakout after 9:30 AM
        breakout_time = self.base_time + datetime.timedelta(minutes=31)  # 9:31 AM
        breakout_price = 101.0  # Clearly above the high of 100.5

        result = self.orb.check_breakout(breakout_time, breakout_price)

        # Should detect a bullish breakout
        self.assertIsNotNone(result)
        direction, entry_price, stop_loss, target = result
        self.assertEqual(direction, Direction.BULLISH)
        self.assertEqual(entry_price, breakout_price)
        self.assertEqual(stop_loss, self.orb.range_midpoint)  # Stop at midpoint
        self.assertEqual(target, entry_price + 2 * (entry_price - stop_loss))  # 1:2 reward

    def test_bearish_breakout_detection(self):
        """Test detection of bearish breakout."""
        # Establish opening range (9:15-9:30)
        base_price = 100.0
        for i in range(15):
            timestamp = self.base_time + datetime.timedelta(minutes=i)
            # Oscillate between 99.5 and 100.5
            price = base_price + ((-1) ** i) * 0.5
            self.orb.add_tick(timestamp, price)

        # Lock the range by adding a tick after 9:30 AM
        self.orb.add_tick(self.base_time + datetime.timedelta(minutes=16), 100.0)

        # Verify range is established
        self.assertAlmostEqual(self.orb.opening_range_low, 99.5, places=1)
        self.assertAlmostEqual(self.orb.opening_range_high, 100.5, places=1)
        self.assertAlmostEqual(self.orb.range_midpoint, 100.0, places=1)

        # Now simulate a bearish breakout after 9:30 AM
        breakout_time = self.base_time + datetime.timedelta(minutes=31)  # 9:31 AM
        breakout_price = 99.0  # Clearly below the low of 99.5

        result = self.orb.check_breakout(breakout_time, breakout_price)

        # Should detect a bearish breakout
        self.assertIsNotNone(result)
        direction, entry_price, stop_loss, target = result
        self.assertEqual(direction, Direction.BEARISH)
        self.assertEqual(entry_price, breakout_price)
        self.assertEqual(stop_loss, self.orb.range_midpoint)  # Stop at midpoint
        self.assertEqual(target, entry_price - 2 * (stop_loss - entry_price))  # 1:2 reward

    def test_no_breakout_within_range(self):
        """Test that no breakout is detected when price stays within range."""
        # Establish opening range
        base_price = 100.0
        for i in range(15):
            timestamp = self.base_time + datetime.timedelta(minutes=i)
            price = base_price + ((-1) ** i) * 0.3  # Stay within 99.7-100.3
            self.orb.add_tick(timestamp, price)

        # Lock the range
        self.orb.add_tick(self.base_time + datetime.timedelta(minutes=16), 100.0)

        # Test prices within range - should not trigger breakout
        test_prices = [99.8, 100.0, 100.2]
        for price in test_prices:
            timestamp = self.base_time + datetime.timedelta(minutes=31)
            result = self.orb.check_breakout(timestamp, price)
            self.assertIsNone(result, f"Should not detect breakout at price {price}")

    def test_breakout_calculation_accuracy(self):
        """Test that breakout calculations are accurate."""
        # Establish a clear opening range
        self.orb.opening_range_high = 100.0
        self.orb.opening_range_low = 98.0
        self.orb.range_midpoint = 99.0
        self.orb.is_range_locked = True

        # Bullish breakout test
        breakout_price = 101.0
        result = self.orb.check_breakout(datetime.datetime.now(), breakout_price)
        self.assertIsNotNone(result)
        direction, entry_price, stop_loss, target = result
        self.assertEqual(direction, Direction.BULLISH)
        self.assertEqual(entry_price, 101.0)
        self.assertEqual(stop_loss, 99.0)  # Midpoint
        self.assertEqual(target, 105.0)  # 101 + 2*(101-99) = 101 + 4 = 105

        # Bearish breakout test
        breakout_price = 97.0
        result = self.orb.check_breakout(datetime.datetime.now(), breakout_price)
        self.assertIsNotNone(result)
        direction, entry_price, stop_loss, target = result
        self.assertEqual(direction, Direction.BEARISH)
        self.assertEqual(entry_price, 97.0)
        self.assertEqual(stop_loss, 99.0)  # Midpoint
        self.assertEqual(target, 93.0)  # 97 - 2*(99-97) = 97 - 4 = 93

    def test_get_range_info(self):
        """Test the get_range_info method."""
        # Add some test data
        self.orb.add_tick(self.base_time, 100.0)
        self.orb.add_tick(self.base_time + datetime.timedelta(minutes=1), 101.0)

        info = self.orb.get_range_info()
        self.assertEqual(info["symbol"], self.symbol)
        self.assertEqual(info["tick_count"], 2)
        self.assertEqual(info["opening_range_high"], 101.0)
        self.assertEqual(info["opening_range_low"], 100.0)
        self.assertFalse(info["is_range_locked"])


if __name__ == "__main__":
    unittest.main()