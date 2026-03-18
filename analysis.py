import pandas as pd
import numpy as np
import config
import sqlite3
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


# सुनिश्चित folders exist
def create_folders():
    os.makedirs("analysis", exist_ok=True)


def load_data():
    try:
        conn = sqlite3.connect(config.DB_NAME)
        df = pd.read_sql_query("SELECT * FROM prices ORDER BY date ASC", conn)
        conn.close()

        if df.empty:
            print("No data found in database.")
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(['coin_id', 'date'])
        return df

    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


def organize_data(df):
    price_table = df.pivot(index='date', columns='coin_id', values='price')
    price_table = price_table.ffill().dropna()
    return price_table


def calculate(price_table):
    # returns
    returns = price_table.pct_change().dropna()

    # average returns (UNCHANGED)
    avg_returns = returns.mean() * 365

    # volatility
    volatility = returns.std() * np.sqrt(365)

    # sharpe ratio
    sharpe_ratio = avg_returns / volatility

    # correlation
    correlation = returns.corr()

    # covariance
    covariance = returns.cov() * 365

    summary = pd.DataFrame({
        'Average Return': avg_returns,
        'Volatility': volatility,
        'Sharpe Ratio': sharpe_ratio
    }).sort_values('Sharpe Ratio', ascending=False)

    return summary, returns, correlation, covariance


# ------------------- PLOTS -------------------

def plot_prices(price_table):
    df_long = price_table.reset_index().melt(id_vars='date',
                                             var_name='coin_id',
                                             value_name='price')

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_long, x='date', y='price', hue='coin_id')
    plt.title("Price Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend(title="Coin")
    plt.tight_layout()
    plt.savefig("analysis/price_trends.png")
    plt.close()


# NEW: individual coin plots
def plot_individual_prices(price_table):
    for coin in price_table.columns:
        plt.figure(figsize=(10, 5))
        plt.plot(price_table.index, price_table[coin])
        plt.title(f"{coin} Price Trend")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.tight_layout()
        plt.savefig(f"analysis/{coin}_price.png")
        plt.close()


def plot_return_distribution(returns):
    df_long = returns.reset_index().melt(id_vars='date',
                                         var_name='coin_id',
                                         value_name='daily_return')

    plt.figure(figsize=(12, 6))
    sns.histplot(data=df_long, x="daily_return",
                 hue="coin_id", kde=True, bins=50)
    plt.title("Daily Return Distribution")
    plt.xlabel("Daily Return")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("analysis/return_distribution.png")
    plt.close()


def plot_correlation(correlation_matrix):
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True,
                cmap="coolwarm", center=0)
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.savefig("analysis/correlation_matrix.png")
    plt.close()


def plot_risk_return(summary):
    plt.figure(figsize=(8, 6))
    plt.scatter(summary['Volatility'], summary['Average Return'], s=100)

    for coin in summary.index:
        plt.annotate(
            coin,
            (summary.loc[coin, 'Volatility'],
             summary.loc[coin, 'Average Return']),
            xytext=(5, 5),
            textcoords='offset points'
        )

    plt.xlabel("Annual Volatility (Risk)")
    plt.ylabel("Annual Return")
    plt.title("Risk vs Return")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("analysis/risk_return.png")
    plt.close()


# ------------------- NEW ANALYSIS -------------------

def calculate_drawdown(price_table):
    cumulative = (1 + price_table.pct_change()).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return drawdown


def plot_drawdown(drawdown):
    plt.figure(figsize=(10, 6))
    drawdown.plot()
    plt.title("Drawdown Over Time")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.savefig("analysis/drawdown.png")
    plt.close()


def rolling_volatility(returns, window=30):
    return returns.rolling(window).std() * np.sqrt(365)


def plot_rolling_volatility(rolling_vol):
    plt.figure(figsize=(10, 6))
    rolling_vol.plot()
    plt.title("Rolling Volatility (30 Days)")
    plt.xlabel("Date")
    plt.ylabel("Volatility")
    plt.tight_layout()
    plt.savefig("analysis/rolling_volatility.png")
    plt.close()


# ------------------- MAIN -------------------

def analysis():
    create_folders()

    df = load_data()
    if df.empty:
        print("No data to analyze.")
        return

    price_table = organize_data(df)

    summary, returns, correlation, covariance = calculate(price_table)

    print("\nSummary Statistics:")
    print(summary)

    # plots
    plot_prices(price_table)
    plot_individual_prices(price_table)   # NEW
    plot_return_distribution(returns)
    plot_correlation(correlation)
    plot_risk_return(summary)

    # new analytics
    drawdown = calculate_drawdown(price_table)
    plot_drawdown(drawdown)

    rolling_vol = rolling_volatility(returns)
    plot_rolling_volatility(rolling_vol)

    # save outputs
    summary.to_csv("analysis/analysis_summary.csv")
    returns.to_csv("analysis/daily_returns.csv")
    covariance.to_csv("analysis/covariance.csv")
    drawdown.to_csv("analysis/drawdown.csv")
    rolling_vol.to_csv("analysis/rolling_volatility.csv")

    print("\nAnalysis complete. All outputs saved in 'analysis/' folder.")


if __name__ == "__main__":
    analysis()