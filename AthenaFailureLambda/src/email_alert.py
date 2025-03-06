# src/email_alert.py

def send_alert_email(query_result, config, ses_client):
    alert_level = query_result.get("alert_level")
    if alert_level == "CRITICAL":
        subject_data = "Critical: SMS Failure Alert"
    elif alert_level == "WARNING":
        subject_data = "Warning: SMS Failure Alert"
    else:
        subject_data = "Cleared: SMS Failure Alert"

    total_messages = query_result.get("total_messages", 0)
    failed_messages = query_result.get("failed_messages", 0)
    failure_rate = query_result.get("failure_rate", 0)

    body_data = (
        f"Alert Level: {alert_level}\n"
        f"Total Messages: {total_messages}\n"
        f"Failed Messages: {failed_messages}\n"
        f"Failure Rate: {failure_rate}%\n"
    )

    response = ses_client.send_email(
        Source = config["source_email"],
        Destination={"ToAddresses": config["recipients"]},
        Message={
            "Subject": {"Data": subject_data},
            "Body": {"Text": {"Data": body_data}}
        }
    )

    return response
