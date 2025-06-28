import datetime
from app.utils.current_date import current_date


def test_current_date_fixed(monkeypatch):
    class FixedDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz):
            return cls(2021, 12, 31, tzinfo=tz)

    monkeypatch.setattr("datetime.datetime", FixedDateTime)
    result = current_date()
    assert result == "Current date: 2021-12-31"
