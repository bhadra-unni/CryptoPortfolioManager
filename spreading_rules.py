import pandas as pd
import numpy as np

def calculate_rebalance(current_portfolio, target_allocation, threshold=0.05):
   
    #Detects portfolio drift and suggests buy/sell trades.
    #compare current portfolio against target alloocation and identifies coins that have drifted beyond the specified threshold.
    cp = current_portfolio.copy()
    cp['Current Value ($)'] = cp['Units'] * cp['Current Price']
    total_value = cp['Current Value ($)'].sum()

    #calcualte what percent of money is cuurently in each coin
    cp['Actual Weight (%)'] = (cp['Current Value ($)'] / total_value) * 100

    ta = target_allocation[['Coin', 'Weight (%)']].copy()
    ta = ta.rename(columns={'Weight (%)': 'Target Weight (%)'})

    #merge and compare
    comparison = pd.merge(cp, ta, on='Coin', how='inner')
    actions = []

    for _, row in comparison.iterrows():
        actual_w = row['Actual Weight (%)']
        target_w = row['Target Weight (%)']
        drift = actual_w - target_w

        if abs(drift) > (threshold * 100):
            target_dollar_val = (target_w / 100) * total_value
            difference = target_dollar_val - row['Current Value ($)']
            actions.append({
                "Coin": row['Coin'],
                "Action": "BUY" if difference > 0 else "SELL",
                "Amount ($)": round(abs(difference), 2),
                "Units": round(abs(difference / row['Current Price']), 6),
                "Drift (%)": round(drift, 2)
            })

    return pd.DataFrame(actions)

def simulate_market_setup(portfolio, setup_type="crash"):
    #Simulates market conditions to test portfolio resilience.
    stressed = portfolio.copy()
    if setup_type == "crash":
        stressed['Current Price'] *= 0.70
    elif setup_type == "bull":
        stressed['Current Price'] *= 1.40
    elif setup_type == "volatility":
        noise = np.random.normal(0, 0.15, len(stressed))
        stressed['Current Price'] *= (1 + noise)
    return stressed

def evaluate_portfolio(portfolio):
    """
    Calculates total portfolio value. Required by main.py.
    """
    return (portfolio['Units'] * portfolio['Current Price']).sum()