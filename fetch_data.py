import requests
import time
import logging
import config
import database
from datetime import datetime

# Setup professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data(coin_id, session):
    url = f"{config.BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": config.DAYS, "interval": "daily"}
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": config.API_KEY,
        "User-Agent": "CryptoManager/1.0"
    }

    # Exponential backoff: waits longer after each failure
    for attempt in range(3): 
        try:
            response = session.get(url, params=params, headers=headers, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                prices = data.get("prices", [])
                
                clean_data = []
                existing_dates = database.get_existing_dates(coin_id)
                
                for i in range(len(prices)):
                    timestamp = prices[i][0]
                    date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                    if date_str in existing_dates: continue
                    
                    clean_data.append({
                        "coin_id": coin_id,
                        "date": date_str,
                        "price": prices[i][1],
                        "market_cap": data["market_caps"][i][1] if i < len(data["market_caps"]) else 0,
                        "volume": data["total_volumes"][i][1] if i < len(data["total_volumes"]) else 0
                    })
                return clean_data

            elif response.status_code == 429:
                wait = (attempt + 1) * 30
                logging.warning(f"Rate limited for {coin_id}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logging.error(f"API Error {response.status_code} for {coin_id}")
                break

        except Exception as e:
            logging.error(f"Connection error for {coin_id}: {e}")
            time.sleep(5)
            
    return []