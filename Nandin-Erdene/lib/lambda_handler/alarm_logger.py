import json
import boto3
import time
import os
from datetime import datetime, timezone

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("TABLE_NAME")


def lambda_handler(event, context):
    """
    This Lambda is subscribed to SNS.
    It logs CloudWatch alarm events into DynamoDB.
    """
    print("Received event:", json.dumps(event))

    if not TABLE_NAME:
        raise Exception("TABLE_NAME environment variable not set")

    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):
        sns_message = record.get("Sns", {})
        try:
            message = json.loads(sns_message.get("Message", "{}"))
        except Exception:
            message = {"RawMessage": sns_message.get("Message")}

        alarm_name = message.get("AlarmName", "UnknownAlarm")
        new_state = message.get("NewStateValue", "UNKNOWN")
        reason = message.get("NewStateReason", sns_message.get("Message", "No reason provided"))

        # Use timezone-aware UTC timestamp
        timestamp = datetime.now(timezone.utc).isoformat()

        table.put_item(
            Item={
                "AlarmName": alarm_name,
                "Timestamp": timestamp,
                "State": new_state,
                "Reason": reason
            }
        )

        print(f"Logged alarm {alarm_name} to DynamoDB at {timestamp}")

    return {"status": "success"}
