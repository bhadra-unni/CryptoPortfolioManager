import smtplib
from email.mime.text import MIMEText
import config


def send_alert_email(risk_results):

    if not risk_results:
        print("No major risks detected.")
        return

    body = "Crypto Risk Alert!\n\nDetected Issues:\n"
    #Generate email body with risk details
    for coin, r_type, val in risk_results:
        body += f"- {coin}: {r_type} ({val})\n"

    #Convert text body into proper formatted email
    msg = MIMEText(body)

    msg["Subject"] = "CRYPTO ALERT: Market Risk Detected"
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECEIVER

    try:
        #Connects to Gmail's SMTP server securely and sends the email alert
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.send_message(msg)

        print("Alert email sent successfully.")

    except Exception as e:

        print(f"Email failed: {e}")