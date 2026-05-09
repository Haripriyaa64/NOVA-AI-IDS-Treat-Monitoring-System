import sqlite3
import pandas as pd
from ml_detector import train_ml_model

DB_PATH = "nova.db"

conn = sqlite3.connect(DB_PATH)

logs = pd.read_sql_query("SELECT * FROM login_logs", conn)

conn.close()

if logs.empty:
    print("No login logs found.")
    exit()

features = []

for ip in logs["source_ip"].unique():
    ip_logs = logs[logs["source_ip"] == ip]

    failed_count = len(ip_logs[ip_logs["login_status"] == "FAILED"])
    success_count = len(ip_logs[ip_logs["login_status"] == "SUCCESS"])
    total_attempts = len(ip_logs)
    unique_emails = ip_logs["email"].nunique()

    features.append({
        "failed_count": failed_count,
        "success_count": success_count,
        "total_attempts": total_attempts,
        "unique_emails": unique_emails
    })

features_df = pd.DataFrame(features)

train_ml_model(features_df)

print("ML model trained and saved successfully.")