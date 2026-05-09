import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

MODEL_PATH = "ids_ml_model.pkl"


def train_ml_model(logs_df):
    """
    Trains ML anomaly model using login_logs data.
    """

    if logs_df.empty:
        return None

    features = logs_df[[
        "failed_count",
        "total_attempts",
        "unique_emails",
        "success_count"
    ]]

    model = IsolationForest(
        contamination=0.2,
        random_state=42
    )

    model.fit(features)

    joblib.dump(model, MODEL_PATH)

    return model


def predict_anomaly(failed_count, total_attempts, unique_emails, success_count):
    """
    Predicts whether login behavior is normal or suspicious.
    """

    try:
        model = joblib.load(MODEL_PATH)
    except:
        return "MODEL_NOT_FOUND"

    data = pd.DataFrame([{
        "failed_count": failed_count,
        "total_attempts": total_attempts,
        "unique_emails": unique_emails,
        "success_count": success_count
    }])

    prediction = model.predict(data)[0]

    if prediction == -1:
        return "SUSPICIOUS"

    return "NORMAL"