import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

import analysis
import investment_mix
import predictor
import risk_checker
import spreading_rules

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CryptoSphere — Portfolio Intelligence",
    layout="wide",
)

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key in ["analysis_run", "price_table", "summary", "returns",
            "correlation", "predictions", "risks", "latest_prices"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "analysis_run" not in st.session_state:
    st.session_state["analysis_run"] = False

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def risk_level(vol):
    if vol < 0.6:
        return "Low"
    elif vol < 0.9:
        return "Medium"
    else:
        return "High"

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("📊 Crypto Portfolio Manager")
st.caption("Smart analysis • Risk insights • Portfolio optimization")

# ─────────────────────────────────────────────
# TOP-LEVEL ANALYSIS BUTTON
# ─────────────────────────────────────────────
col_btn, col_status = st.columns([2, 5])
with col_btn:
    run_analysis = st.button("⟳ Load & Analyse Market Data")

with col_status:
    if not st.session_state["analysis_run"]:
        st.info("Click the button to load data from the database and run analysis.")
    else:
        st.success("✓ Market data loaded. All sections are live.")

if run_analysis:
    with st.spinner("Loading data and running analysis…"):
        df = analysis.load_data()
        if df.empty:
            st.error("No data found. Run the data fetcher first.")
            st.stop()

        price_table = analysis.organize_data(df)
        summary, returns, correlation, _ = analysis.calculate(price_table)
        latest_prices = price_table.iloc[-1]

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_pred = ex.submit(predictor.predict_future_returns, returns, 30)
            f_risk = ex.submit(risk_checker.run_parallel_risk_checks, price_table, returns)
            predictions = f_pred.result()
            risks       = f_risk.result()

        st.session_state.update({
            "analysis_run": True,
            "price_table":  price_table,
            "summary":      summary,
            "returns":      returns,
            "correlation":  correlation,
            "predictions":  predictions,
            "risks":        risks,
            "latest_prices": latest_prices,
        })
    st.rerun()

if not st.session_state["analysis_run"]:
    st.stop()

# ─────────────────────────────────────────────
# GRAB STATE
# ─────────────────────────────────────────────
price_table   = st.session_state["price_table"]
summary       = st.session_state["summary"]
returns       = st.session_state["returns"]
correlation   = st.session_state["correlation"]
predictions   = st.session_state["predictions"]
risks         = st.session_state["risks"]
latest_prices = st.session_state["latest_prices"]

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_analysis, tab_risk, tab_mix, tab_rebalance, tab_predict = st.tabs([
    "📊 Analysis",
    "⚠️ Risk Check",
    "💡 Investment Mix",
    "⚖️ Rebalance",
    "🔮 Predictions",
])

# ══════════════════════════════════════════════
# TAB 1 — ANALYSIS
# ══════════════════════════════════════════════
with tab_analysis:
    st.subheader("Market Summary")

    # KPI row
    n_coins   = len(summary)
    best_coin = summary["Sharpe Ratio"].idxmax()
    avg_vol   = summary["Volatility"].mean()
    avg_ret   = summary["Average Return"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Coins Tracked", n_coins)
    c2.metric("Best Coin (Sharpe)", best_coin.upper())
    c3.metric("Avg Return", f"{avg_ret*100:.2f}%")
    c4.metric("Avg Volatility", f"{avg_vol*100:.2f}%")

    st.subheader("Coin Statistics")
    summary_display = summary.copy()
    summary_display["Latest Price"] = latest_prices
    summary_display["Return (%)"] = summary_display["Average Return"] * 100
    summary_display["Volatility (%)"] = summary_display["Volatility"] * 100
    st.dataframe(summary_display, use_container_width=True)

    st.subheader("Price Trends")
    price_norm = price_table / price_table.iloc[0] * 100
    st.line_chart(price_norm)

# ══════════════════════════════════════════════
# TAB 2 — RISK CHECK
# ══════════════════════════════════════════════
with tab_risk:
    st.subheader("Risk Alerts")
    if not risks:
        st.success("No major risks detected")
    else:
        for coin, r_type, val in risks:
            st.warning(f"{coin.upper()} → {r_type} ({val})")

    # Optional simple risk table
    risk_df = summary[["Volatility"]].copy()
    risk_df["Risk Level"] = risk_df["Volatility"].apply(risk_level)
    st.dataframe(risk_df, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — INVESTMENT MIX
# ══════════════════════════════════════════════
with tab_mix:
    st.subheader("Configure Your Investment")
    total_investment = st.number_input("Total Investment ($)", min_value=50.0, value=5000.0, step=100.0)
    risk_profile = st.selectbox("Risk Profile", ["Conservative", "Balanced", "Aggressive"], index=1)
    max_coins = st.slider("Max Coins to Hold", min_value=2, max_value=min(10, len(summary)), value=5)

    if st.button("Generate Investment Mix"):
        mix_df = investment_mix.calculate_mix(total_investment, risk_profile.lower(), max_coins, summary, latest_prices)
        if mix_df is not None and not mix_df.empty:
            st.dataframe(mix_df, use_container_width=True)
        else:
            st.error("Could not generate a mix. Adjust parameters.")

# ══════════════════════════════════════════════
# TAB 4 — REBALANCE
# ══════════════════════════════════════════════
with tab_rebalance:
    st.subheader("Enter Your Current Holdings")
    available_coins = sorted(price_table.columns.tolist())
    selected_coins  = st.multiselect("Select coins you hold", options=available_coins, default=available_coins[:3])

    if selected_coins:
        holdings_input = {}
        cols = st.columns(min(len(selected_coins), 4))
        for i, coin in enumerate(selected_coins):
            with cols[i % len(cols)]:
                units = st.number_input(f"{coin.upper()} Units", min_value=0.0, value=0.1, step=0.001, format="%.6f")
                holdings_input[coin] = units

        total_val = sum(units * latest_prices[coin] for coin, units in holdings_input.items())
        current_df = pd.DataFrame([{
            "Coin": coin,
            "Units": units,
            "Current Price": latest_prices[coin],
            "Current Value ($)": units * latest_prices[coin]
        } for coin, units in holdings_input.items()])
        current_df["Actual Weight (%)"] = current_df["Current Value ($)"] / total_val * 100

        st.dataframe(current_df, use_container_width=True)

        # Rebalance target
        reb_profile = st.selectbox("Target Risk Profile", ["Conservative", "Balanced", "Aggressive"], index=1)
        reb_max_coins = st.slider("Target Max Coins", min_value=2, max_value=len(selected_coins), value=min(len(selected_coins),5))
        target_df = investment_mix.calculate_mix(total_val, reb_profile.lower(), reb_max_coins, summary, latest_prices)
        if target_df is not None and not target_df.empty:
            st.dataframe(target_df, use_container_width=True)

            # Compute simple actions
            actions = []
            for _, r in current_df.iterrows():
                coin = r["Coin"]
                tgt_w = target_df.loc[target_df["Coin"]==coin, "Weight (%)"].values[0] if not target_df[target_df["Coin"]==coin].empty else 0
                drift = r["Actual Weight (%)"] - tgt_w
                if abs(drift) > 5.0:
                    difference = (tgt_w/100)*total_val - r["Current Value ($)"]
                    actions.append({
                        "Coin": coin.upper(),
                        "Action": "BUY" if difference>0 else "SELL",
                        "Amount ($)": round(abs(difference),2),
                        "Units": round(abs(difference/r["Current Price"]),6),
                        "Drift (%)": round(drift,2)
                    })

            if actions:
                st.subheader("Rebalance Actions")
                st.dataframe(pd.DataFrame(actions), use_container_width=True)
            else:
                st.success("Portfolio is balanced within 5% drift.")

# ══════════════════════════════════════════════
# TAB 5 — PREDICTIONS
# ══════════════════════════════════════════════
with tab_predict:
    st.subheader("30-Day Return Predictions")

    sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
    pred_df = pd.DataFrame(sorted_preds, columns=["Coin", "Prediction (%)"])
    st.dataframe(pred_df, use_container_width=True)
    if pred_df.shape[0]>0:
        top_pick = pred_df.iloc[0]["Coin"]
        st.success(f"Top Predicted Pick: {top_pick.upper()}")

    st.bar_chart(pred_df.set_index("Coin"))