from datetime import datetime, timedelta, timezone

from screenpipe_client.time_utils import format_timestamp, get_past_time


def test_get_past_time_is_utc():
    stamp = datetime.strptime(get_past_time(hours=1), "%Y-%m-%dT%H:%M:%SZ")
    expected = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    assert abs((stamp - expected).total_seconds()) < 5


def test_format_timestamp():
    assert format_timestamp("2024-10-01T12:00:00.123Z") == "10/01/24 12:00"
    assert format_timestamp("2024-10-01T12:00:00Z", offset_hours=-7) == "10/01/24 05:00"
