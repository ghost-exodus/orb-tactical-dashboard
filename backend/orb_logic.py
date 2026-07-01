import datetime
from typing import List, Tuple, Optional
from enum import Enum


class Direction(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class ORBEngine:
    """
    Opening Range Breakout (ORB) Engine

    Calculates the opening range (first 15 minutes) and detects breakouts.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.opening_range_high: Optional[float] = None
        self.opening_range_low: Optional[float] = None
        self.range_midpoint: Optional[float] = None
        self.is_range_locked = False
        self.ticks: List[Tuple[datetime.datetime, float]] = []

    def add_tick(self, timestamp: datetime.datetime, price: float) -> None:
        """
        Add a price tick to the engine.

        Args:
            timestamp: The timestamp of the tick
            price: The price value
        """
        self.ticks.append((timestamp, price))

        # If we haven't locked the range yet and we're within the first 15 minutes
        if not self.is_range_locked:
            # Define market open time (9:15 AM IST) and range end time (9:30 AM IST)
            market_open = timestamp.replace(hour=9, minute=15, second=0, microsecond=0)
            range_end = timestamp.replace(hour=9, minute=30, second=0, microsecond=0)

            # If we're within the opening range period (9:15-9:30)
            if market_open <= timestamp <= range_end:
                # Update high and low for the opening range
                if self.opening_range_high is None or price > self.opening_range_high:
                    self.opening_range_high = price
                if self.opening_range_low is None or price < self.opening_range_low:
                    self.opening_range_low = price
            # If we've passed the range end time, lock the range
            elif timestamp > range_end:
                self._lock_range()

    def _lock_range(self) -> None:
        """Lock the opening range after 9:30 AM."""
        if self.opening_range_high is not None and self.opening_range_low is not None:
            self.is_range_locked = True
            self.range_midpoint = (self.opening_range_high + self.opening_range_low) / 2

    def check_breakout(self, timestamp: datetime.datetime, price: float) -> Optional[Tuple[Direction, float, float, float]]:
        """
        Check if the current price represents a breakout from the opening range.

        Args:
            timestamp: The timestamp of the tick
            price: The current price

        Returns:
            Tuple of (direction, breakout_price, stop_loss, target) if breakout detected,
            None otherwise
        """
        # Only check for breakouts after the range is locked (after 9:30 AM)
        if not self.is_range_locked:
            return None

        # Calculate risk management levels
        if self.opening_range_high is None or self.opening_range_low is None or self.range_midpoint is None:
            return None

        # Check for bullish breakout (price > opening range high)
        if price > self.opening_range_high:
            entry_price = price
            stop_loss = self.range_midpoint  # Structural stop-loss at midpoint
            target = entry_price + 2 * (entry_price - stop_loss)  # 1:2 risk-reward
            return (Direction.BULLISH, entry_price, stop_loss, target)

        # Check for bearish breakout (price < opening range low)
        if price < self.opening_range_low:
            entry_price = price
            stop_loss = self.range_midpoint  # Structural stop-loss at midpoint
            target = entry_price - 2 * (stop_loss - entry_price)  # 1:2 risk-reward
            return (Direction.BEARISH, entry_price, stop_loss, target)

        return None

    def get_range_info(self) -> dict:
        """
        Get the current opening range information.

        Returns:
            Dictionary with range information
        """
        return {
            "symbol": self.symbol,
            "opening_range_high": self.opening_range_high,
            "opening_range_low": self.opening_range_low,
            "range_midpoint": self.range_midpoint,
            "is_range_locked": self.is_range_locked,
            "tick_count": len(self.ticks)
        }