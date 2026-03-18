import pandas as pd
import os


def generate_final_report(summary, predictions, risks):

    os.makedirs("reports", exist_ok=True)

    # Investment report
    report_df = summary.copy()

    report_df["Predicted 30d Return (%)"] = report_df.index.map(predictions)

    report_df.to_csv("reports/investment_report.csv")

    # Risk report
    # Only generate if there are risks to report
    if risks:

        risk_df = pd.DataFrame(risks, columns=["Coin", "Risk Type", "Value"])

        risk_df.to_csv("reports/risk_report.csv", index=False)

    print("Reports saved in /reports folder.")