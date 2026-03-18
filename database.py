import sqlite3, pandas as pd, config

def setup_db():
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            coin_id TEXT,
            date TEXT,
            price REAL,
            market_cap REAL,
            volume REAL,
            PRIMARY KEY (coin_id, date)
        )
    ''')
    conn.commit()
    conn.close()

def get_existing_dates(coin_id):
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT date FROM prices WHERE coin_id = ?', (coin_id,))
    existing_dates = {row[0] for row in cursor.fetchall()}
    conn.close()
    return existing_dates

def save_db(data_list):
    if not data_list: return
    conn = sqlite3.connect(config.DB_NAME)
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR IGNORE INTO prices (coin_id, date, price, market_cap, volume)
        VALUES (:coin_id, :date, :price, :market_cap, :volume)
    ''', data_list)
    conn.commit()
    conn.close()
    print(f"Saved {len(data_list)} records to database.")

def export_to_csv(all_data):
    conn = sqlite3.connect(config.DB_NAME)
    df = pd.read_sql_query("SELECT * FROM prices ORDER BY date DESC", conn)
    conn.close()
    
    if not df.empty:
        df.to_csv(config.CSV, index=False)
        print(f"CSV Updated: {config.CSV} ({len(df)} total unique rows)")
def save_trends_to_db(summary_df):
    conn = sqlite3.connect(config.DB_NAME)
    # Save the summary statistics (trends) to a new table
    summary_df.to_sql('market_trends', conn, if_exists='replace', index=True, index_label='coin_id')
    conn.close()
    print("Trends saved to database table 'market_trends'.")