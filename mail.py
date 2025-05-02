# email_utils.py
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_alert_email(subject, message):
    email = "xyz@gmail.com" 
    password = "xxxxxxx"

    df = pd.read_excel("contacts.xlsx", header=None)
    names = df.iloc[:, 0].tolist()
    recipient_list = df.iloc[:, 1].tolist()

    for recipient, name in zip(recipient_list, names):
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(f"Dear {name},\n\n{message}\n\nRegards,\nYour Team", "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, recipient, msg.as_string())
            print(f"✅ Email sent to {recipient}")
        except Exception as e:
            print(f"❌ Error sending email to {recipient}: {str(e)}")
        finally:
            server.quit()
