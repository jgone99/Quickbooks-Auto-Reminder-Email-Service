import json
from datetime import date
from config import SENT_LOG_PATH

# records which customers have been sent this week's report, so a rerun after a
# failed or interrupted run only sends to the customers that were missed

def _current_week() -> str:
    # e.g. 2026-W42
    year, week, _ = date.today().isocalendar()
    return f"{year}-W{week:02d}"

def load_sent_this_week() -> set[str]:
    if not SENT_LOG_PATH.exists():
        return set()

    # invalid JSON raises, so a corrupted log can't cause every customer to be emailed again
    data = json.loads(SENT_LOG_PATH.read_text(encoding="utf-8"))

    if data.get("week") != _current_week():
        return set()

    return set(data.get("customer_ids", []))

def record_sent(customer_id: str):
    # written after every send so an interrupted run still has an accurate record
    sent = load_sent_this_week()
    sent.add(customer_id)

    SENT_LOG_PATH.write_text(
        json.dumps({"week": _current_week(), "customer_ids": sorted(sent)}, indent=4),
        encoding="utf-8"
    )
