from datetime import date, datetime

from app.utils.dates import default_24_month_range


def test_default_range_uses_24_calendar_months() -> None:
    date_from, date_to = default_24_month_range(datetime(2025, 12, 18, 10, 30))

    assert date_from == date(2024, 1, 1)
    assert date_to == date(2025, 12, 18)
