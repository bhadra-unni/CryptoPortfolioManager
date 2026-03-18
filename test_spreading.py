# test_spreading.py
import pandas as pd
import spreading_rules

# Mock Target from Investment Mix
target = pd.DataFrame({
    'Coin': ['bitcoin', 'ethereum'],
    'Weight (%)': [50.0, 50.0]
})

# Mock Portfolio that has drifted (Bitcoin outperformed)
current = pd.DataFrame({
    'Coin': ['bitcoin', 'ethereum'],
    'Units': [0.5, 10.0],
    'Current Price': [100000, 2000] # Total Value = 50k + 20k = 70k
})

# BTC is now ~71% of portfolio, ETH is ~29%. Drift is ~21%
rebalance = spreading_rules.calculate_rebalance(current, target)

print("--- REBALANCING REPORT ---")
if not rebalance.empty:
    print(rebalance.to_string(index=False))
else:
    print("Portfolio is healthy. No trades needed.")