

# import time, requests
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import config
# import database
# import fetch_data
# import analysis        
# import investment_mix  , predictor, risk_checker, email_alert, report_generator

# def main():
#     start_time = time.time()
#     database.setup_db()
#     all_data = []

#     print(f"\nStarted Parallel Fetch")
#     session = requests.Session()
#     with ThreadPoolExecutor(max_workers= 2) as executor:

#         future_to_coin = {
#             executor.submit(fetch_data.fetch_data, coin, session): coin 
#             for coin in config.COINS
#         }
        
#         for future in as_completed(future_to_coin):
#             coin_id = future_to_coin[future]
#             try:
#                 data = future.result()
#                 if data:
#                     all_data.extend(data)
#                     print(f"Finished: {coin_id}({len(data)} new records)")
#             except Exception as e:
#                 print(f"Worker error on {coin_id}: {e}")

#     # 1. Save new data if we found any
#     if all_data:
#         database.save_db(all_data)
#         database.export_to_csv(all_data)
#         print(f"\nProcessed {len(all_data)} new records.")
#     else:
#         print("\nNo new data collected. Database is already up to date.")

#     # 2. Always run the analysis on the database
#     print("\n--- Running Market Analysis ---")
#     analysis.analysis()



#     # 3. Always run the investment mix calculator
#     print("\n--- Generating Investment Mix ---")
#     investment_mix.main()

#     total_time = time.time() - start_time
#     print(f"\nTotal execution time: {total_time:.2f} seconds.")

# if __name__ == "__main__":
#     main()
import time
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
import database
import fetch_data  # Ensure filename is fetch_data.py
import analysis
import investment_mix
import predictor
import risk_checker
import email_alert
import report_generator
import spreading_rules

def main():
    start_time = time.time()

    # Create necessary folders if they don't exist
    for folder in [config.REPORT_DIR, config.VISUAL_DIR, config.ANALYSIS_DIR]:
        os.makedirs(folder, exist_ok=True)

    # --- STEP 1: Database Setup ---
    database.setup_db()
    all_data = []

    # --- STEP 2: Parallel Data Fetching ---
    print("\n[1/7] Starting Parallel Data Fetch...")
    session = requests.Session()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_coin = {
            executor.submit(fetch_data.fetch_data, coin, session): coin
            for coin in config.COINS
        }

        for future in as_completed(future_to_coin):
            coin_id = future_to_coin[future]
            try:
                data = future.result()
                if data:
                    all_data.extend(data)
                    print(f"  > Finished: {coin_id} ({len(data)} new records)")
            except Exception as e:
                print(f"  > Worker error on {coin_id}: {e}")

    if all_data:
        database.save_db(all_data)
        database.export_to_csv(all_data)
    else:
        print("No new data collected. Database is up to date.")

    # --- STEP 3: Market Analysis ---
    print("\n[2/7] Running Market Analysis...")
    df = analysis.load_data()
    if df.empty:
        print("Error: No data available. Exiting.")
        return

    price_table = analysis.organize_data(df)
    summary, returns, correlation, covariance = analysis.calculate(price_table)
    analysis.plot_prices(price_table)
    analysis.plot_risk_return(summary)

    # --- STEP 4 & 5: Parallel Prediction & Risk Checking ---
    print("\n[3/7 & 4/7] Running Predictions & Risk Checks at the same time...")
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks to run at the same time
        future_predictions = executor.submit(predictor.predict_future_returns, returns, 30)
        future_risks = executor.submit(risk_checker.run_parallel_risk_checks, price_table, returns)
        
        # Gather results
        predictions = future_predictions.result()
        risks = future_risks.result()

    if risks:
        print(f"  > WARNING: {len(risks)} risks detected. Sending email...")
        email_alert.send_alert_email(risks)

    # --- STEP 6: Investment Mix & Reporting ---
    print("\n[5/7] Generating Investment Mix Scenarios...")
    # This calls the interactive main() in investment_mix.py
    investment_mix.main() 

    print("\n[6/7] Saving Final Reports...")
    report_generator.generate_final_report(summary, predictions, risks)

    # --- STEP 7: Stress Tests and Spreading Rules ---
    print("\n[7/7] Running Stress Tests...")
    
    # Calculate a sample 'balanced' mix for the stress test
    target_mix = investment_mix.calculate_mix(
        5000, "balanced", 3, summary, price_table.iloc[-1]
    )

    if target_mix is not None:
        current_portfolio = target_mix.copy()
        current_portfolio["Current Price"] = price_table.iloc[-1][target_mix["Coin"]].values
        current_portfolio["Units"] = current_portfolio["Units to Buy"]
        
        initial_value = spreading_rules.evaluate_portfolio(current_portfolio)

        for scenario in ["crash", "bull"]:
            stressed = spreading_rules.simulate_market_setup(current_portfolio, scenario)
            new_value = spreading_rules.evaluate_portfolio(stressed)
            impact = ((new_value - initial_value) / initial_value) * 100
            
            print(f"\nScenario: {scenario.upper()}")
            print(f"Portfolio Value: ${new_value:.2f} ({impact:.2f}%)")
            
            actions = spreading_rules.calculate_rebalance(stressed, target_mix)
            if not actions.empty:
                print("Rebalancing Actions Required:")
                print(actions.to_string(index=False))

    total_time = time.time() - start_time
    print(f"\n{'='*50}\nSYSTEM EXECUTION COMPLETE in {total_time:.2f}s\n{'='*50}")

if __name__ == "__main__":
    main()