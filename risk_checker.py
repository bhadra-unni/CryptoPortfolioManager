import pandas as pd
from concurrent.futures import ThreadPoolExecutor


def check_volatility_risk(returns, threshold=0.08):
    # Detect coins with high volatility based on standard deviation of returns
    risky = []

    for coin in returns.columns:
        vol = returns[coin].std()
        #if volatility exceeds limit, add to risky list 
        if vol > threshold:
            risky.append((coin, "High Volatility", round(vol, 4)))

    return risky


def check_price_drop_risk(price_table, threshold=-0.10):
    # Detect coins with significant price drops of 10% or more in a single day
    risky = []

    daily_changes = price_table.pct_change()

    for coin in daily_changes.columns:
        min_change = daily_changes[coin].min()

        if min_change < threshold:
            risky.append((coin, "Flash Drop", round(min_change, 4)))

    return risky


def run_parallel_risk_checks(price_table, returns):
    #Runs both risk checking functions simultaneously using ThreadPoolExecutor for efficiency
    results = []

    with ThreadPoolExecutor(max_workers=2) as executor:

        futures = [
            executor.submit(check_volatility_risk, returns),
            executor.submit(check_price_drop_risk, price_table)
        ]

        for future in futures:
            results.extend(future.result())

    return results