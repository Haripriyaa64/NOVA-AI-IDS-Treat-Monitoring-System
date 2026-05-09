from datetime import datetime, timedelta
from models import LoginLog, Alert
from ml_detector import predict_anomaly


def create_alert(db, email, source_ip, attack_type, risk_level, message):
    """
    Creates alert only if same alert is not already present.
    """

    existing_alert = db.query(Alert).filter(
        Alert.source_ip == source_ip,
        Alert.attack_type == attack_type,
        Alert.risk_level == risk_level
    ).first()

    if existing_alert:
        return

    alert = Alert(
        email=email,
        source_ip=source_ip,
        attack_type=attack_type,
        risk_level=risk_level,
        message=message
    )

    db.add(alert)
    db.commit()
# ── Signature Patterns ─────────────────────────────────────────

SQLI_SIGNATURES = [
    "' OR 1=1 --",
    "UNION SELECT",
    "DROP TABLE",
    "'--",
    "' OR '1'='1"
]

XSS_SIGNATURES = [
    "<script>",
    "alert(",
    "onerror=",
    "onload="
]

SCANNER_SIGNATURES = [
    "sqlmap",
    "curl",
    "python-requests",
    "nikto"
]

PATH_TRAVERSAL_SIGNATURES = [
    "../",
    "..\\"
]


def run_ids_rules(db, email, source_ip):
    """
    Rule-based IDS detection.
    It checks login_logs and generates alerts.
    """

    time_window = datetime.utcnow() - timedelta(hours=24)

    recent_logs = db.query(LoginLog).filter(
        LoginLog.source_ip == source_ip,
        LoginLog.created_at >= time_window
    ).all()

    failed_logs = [log for log in recent_logs if log.login_status == "FAILED"]
    success_logs = [log for log in recent_logs if log.login_status == "SUCCESS"]

    failed_count = len(failed_logs)
    total_attempts = len(recent_logs)
    unique_emails = set(log.email for log in recent_logs)
    
    ml_result = predict_anomaly(
    failed_count=failed_count,
    total_attempts=total_attempts,
    unique_emails=len(unique_emails),
    success_count=len(success_logs)
    )

    if ml_result == "SUSPICIOUS":
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="ML-Based Suspicious Behavior",
            risk_level="HIGH",
            message="Machine learning model detected abnormal login behavior."
        )

    # Rule 1: Brute Force Attack
    if failed_count >= 5:
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="Brute Force Attack",
            risk_level="HIGH",
            message=f"{failed_count} failed login attempts detected from same IP within 10 minutes."
        )

    # Rule 2: Credential Stuffing Attack
    if len(unique_emails) >= 3 and failed_count >= 3:
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="Credential Stuffing Attack",
            risk_level="HIGH",
            message=f"Same IP tried {len(unique_emails)} different email accounts."
        )

    # Rule 3: Suspicious Successful Login
    if failed_count >= 3 and len(success_logs) >= 1:
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="Suspicious Successful Login",
            risk_level="MEDIUM",
            message="Successful login detected after multiple failed attempts."
        )

    # Rule 4: Rapid Login Attempts
    if total_attempts >= 10:
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="Rapid Login Attempt",
            risk_level="MEDIUM",
            message=f"{total_attempts} login attempts detected from same IP within 10 minutes."
        )

    # Rule 5: Suspicious Login Behavior
    if failed_count >= 2 and total_attempts >= 5:
        create_alert(
            db=db,
            email=email,
            source_ip=source_ip,
            attack_type="Suspicious Login Behavior",
            risk_level="LOW",
            message="Repeated abnormal login behavior detected."
        )
        
        
def run_signature_detection(db, email, source_ip, user_input, user_agent):

    # SQL Injection Detection
    for signature in SQLI_SIGNATURES:

        if signature.lower() in user_input.lower():

            create_alert(
                db=db,
                email=email,
                source_ip=source_ip,
                attack_type="SQL Injection Attack",
                risk_level="HIGH",
                message=f"SQL Injection signature detected: {signature}"
            )

    # XSS Detection
    for signature in XSS_SIGNATURES:

        if signature.lower() in user_input.lower():

            create_alert(
                db=db,
                email=email,
                source_ip=source_ip,
                attack_type="Cross-Site Scripting (XSS)",
                risk_level="HIGH",
                message=f"XSS signature detected: {signature}"
            )

    # Scanner Tool Detection
    for signature in SCANNER_SIGNATURES:

        if signature.lower() in user_agent.lower():

            create_alert(
                db=db,
                email=email,
                source_ip=source_ip,
                attack_type="Scanner Tool Detected",
                risk_level="MEDIUM",
                message=f"Scanner tool detected: {signature}"
            )

    # Path Traversal Detection
    for signature in PATH_TRAVERSAL_SIGNATURES:

        if signature.lower() in user_input.lower():

            create_alert(
                db=db,
                email=email,
                source_ip=source_ip,
                attack_type="Path Traversal Attack",
                risk_level="HIGH",
                message=f"Path traversal signature detected: {signature}"
            )