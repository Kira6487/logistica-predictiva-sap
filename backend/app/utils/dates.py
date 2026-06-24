from datetime import date, datetime


def _as_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    return date(year, zero_based_month + 1, 1)


def default_24_month_range(max_document_date: date | datetime) -> tuple[date, date]:
    end_date = _as_date(max_document_date)
    start_date = subtract_months(end_date.replace(day=1), 23)
    return start_date, end_date
