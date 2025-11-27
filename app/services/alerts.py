import json
from datetime import datetime
from typing import List, Dict, Any


def send_violation_alert(account_id: str, violations: List[Dict[str, Any]]) -> None:
    """
    Simple alert sender for accounts that violate the 20% rule.

    In a real system, this would publish to SNS/Slack/Email/etc.
    For this exercise, we just format and log the payload.
    """
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": "POSITION_LIMIT_VIOLATION",
        "account_id": account_id,
        "violations": violations,
    }

    # For now: just print. In real life this would be a call to an external service.
    print(f"[ALERT] {json.dumps(payload)}")
