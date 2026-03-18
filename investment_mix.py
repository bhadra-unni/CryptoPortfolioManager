import pandas as pd
import analysis, config

from concurrent.futures import ThreadPoolExecutor, as_completed

def categorize_risk(volatility):
    if volatility < 0.60:
        return "Low"
    elif volatility < 0.90:
        return "Medium"
    else:
        return "High"

def allocation_rules(profile):
    #Defines how much of the portfolio should go into each risk category
    profile = profile.lower()
    if profile == "conservative":
        return {"Low": 0.60, "Medium": 0.30, "High": 0.10}
    elif profile == "aggressive":
        return {"Low": 0.20, "Medium": 0.40, "High": 0.40}
    else: 
        return {"Low": 0.40, "Medium": 0.40, "High": 0.20}

def calculate_mix(total_investment, profile, max_coins, summary, latest_prices):
    
    rules = allocation_rules(profile)
    
    # Group the coins by risk
    coins_by_risk = {"Low": [], "Medium": [], "High": []}
    for coin, row in summary.iterrows():
        category = categorize_risk(row['Volatility'])
        coins_by_risk[category].append({
            "coin_id": coin,
            "expected_return": row['Average Return'],
            "volatility": row['Volatility']
        })
    
    #Decide How Many Coins Per Risk Bucket
    counts = {}
    for cat, pct in rules.items():
        counts[cat] = round(max_coins * pct)
        
    # adjust slots to make sure we don't ask for more coins than a bucket actually has
    for cat in counts:
        if counts[cat] > len(coins_by_risk[cat]):
            counts[cat] = len(coins_by_risk[cat])

    # Ensure total requested coins equals max_coins (redistribute lost slots)
    target_total = min(max_coins, sum(len(c) for c in coins_by_risk.values()))
    
    while sum(counts.values()) > target_total:
        max_cat = max((c for c in counts if counts[c] > 0), key=counts.get)
        counts[max_cat] -= 1
        
    while sum(counts.values()) < target_total:
        # Give the extra slot to the bucket with the highest target % that still has coins
        eligible = [c for c in counts if counts[c] < len(coins_by_risk[c])]
        if not eligible: break
        best_cat = max(eligible, key=lambda c: rules[c])
        counts[best_cat] += 1
    # -------------------------------------------------------------------------
    #if a bucket ens up empty normalize so that weight sum is still 100%
    active_pct_sum = sum(rules[cat] for cat in rules if counts[cat] > 0)

    if active_pct_sum == 0:
        return None
    investable_capital = total_investment * (1 - config.TRADING_FEE)
    allocation_result = []
    
    for category, target_pct in rules.items():
        allowed_count = counts[category]
        
        if allowed_count == 0 or not coins_by_risk[category]:
            continue

        actual_pct = target_pct / active_pct_sum
        #Only highest expected return coins are chosen.
        sorted_coins = sorted(coins_by_risk[category], key=lambda x: x['expected_return'], reverse=True)
        eligible_coins = sorted_coins[:allowed_count]
        #for each category, equal weight insie each risk bucket
        category_budget = total_investment * actual_pct
        amount_per_coin = category_budget / len(eligible_coins)
        weight_per_coin = (actual_pct / len(eligible_coins)) * 100
        
        for coin in eligible_coins:
            coin_name = coin['coin_id']
            
            current_price = latest_prices[coin_name]
            units_to_buy = amount_per_coin / current_price
            
            allocation_result.append({
                "Portfolio": profile.capitalize(),
                "Coin": coin_name,
                "Risk Level": category,
                "Allocated Amount ($)": round(amount_per_coin, 2),
                "Units to Buy": round(units_to_buy, 6),
                "Weight (%)": round(weight_per_coin, 2),
                "Expected Return (%)": round(coin['expected_return'] * 100, 2)
            })
            
    return pd.DataFrame(allocation_result)

def main(total_inv=None, max_c=None):
    try:
        # If no arguments are passed (like when running python main.py), 
        # it will ask for input. If called by Streamlit, it uses the passed values.
        if total_inv is None:
            total_inv = float(input("Enter total investment amount ($): "))
        if max_c is None:
            max_c = int(input("Enter max number of coins to hold (Recommended 3-5): "))
    except ValueError:
        print("Invalid input. Please enter numbers only.")
        return

    print(f"\nAnalyzing data to find your top {max_c} assets...")

    df = analysis.load_data()
    if df.empty:
        print("No data available.")
        return
        
    price_table = analysis.organize_data(df)
    summary, _, _, _ = analysis.calculate(price_table)
    
    latest_prices = price_table.iloc[-1]

    profiles = ["conservative", "balanced", "aggressive"]
    all_results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Notice total_inv and max_c are used here now
        future_to_profile = {
            executor.submit(calculate_mix, total_inv, p, max_c, summary, latest_prices): p 
            for p in profiles
        }
        
        for future in as_completed(future_to_profile):
            p = future_to_profile[future]
            try:
                df_result = future.result()
                if df_result is not None and not df_result.empty:
                    all_results.append(df_result)
                    
                    display_df = df_result.drop(columns=['Portfolio'])
                    print(f"\n{p.upper()} PORTFOLIO :")
                    print("-" * 75)
                    print(display_df.to_string(index=False))
            except Exception as e:
                print(f"Error processing {p}: {e}")

   

if __name__ == "__main__":
    main()