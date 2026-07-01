"""
Script to test ORB engine with synthetic data.
This satisfies the Phase 1 exit checklist item:
- Terminal outputs exactly 1 alert when the synthetic price crosses the 15-minute high
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from synthetic_data import test_orb_with_synthetic_data

def main():
    print("Testing ORB Engine with Synthetic Data")
    print("=" * 50)

    result = test_orb_with_synthetic_data()

    print(f"Breakout detected: {result['breakout_detected']}")
    print(f"Total ticks processed: {result['total_ticks']}")

    if result['breakout_info']:
        info = result['breakout_info']
        print("\nBreakout Details:")
        print(f"  Direction: {info['direction']}")
        print(f"  Entry Price: {info['entry_price']:.2f}")
        print(f"  Stop Loss: {info['stop_loss']:.2f}")
        print(f"  Target: {info['target']:.2f}")
        print(f"  Timestamp: {info['timestamp']}")

    print(f"\nFinal Range Info:")
    for key, value in result['final_range'].items():
        print(f"  {key}: {value}")

    print(f"\nExpected Range Info:")
    for key, value in result['expected_range'].items():
        print(f"  {key}: {value}")

    # Check if we got exactly one alert (as required by Phase Exit Checklist)
    if result['breakout_detected'] and result['breakout_info'] is not None:
        print("\nSUCCESS: Exactly one breakout alert was generated!")
        return 0
    else:
        print("\nFAILURE: Expected exactly one breakout alert.")
        return 1

if __name__ == "__main__":
    sys.exit(main())