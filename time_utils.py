from datetime import datetime, time as _time

class TimeHelper:
    """Utility methods for date/time validation and overtime calculation.

    This module is named `time_utils.py` to avoid conflicts with the builtin `time` module.
    """

    @staticmethod
    def valid_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except Exception:
            return False

    @staticmethod
    def valid_time(time_str: str) -> bool:
        if time_str is None or time_str == '':
            return True
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                datetime.strptime(time_str, fmt)
                return True
            except Exception:
                continue
        return False

    @staticmethod
    def parse_datetime_from_strings(date_str: str, time_str: str):
        if not date_str or not time_str:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(f"{date_str} {time_str}", fmt)
            except Exception:
                continue
        return None

    @staticmethod
    def calculate_overtime_hours(sch_end_time: _time, date_str: str, time_out_str: str):
        if sch_end_time is None or not time_out_str:
            return None
        try:
            y, m, d = map(int, date_str.split('-'))
            sch_end_dt = datetime.combine(datetime(year=y, month=m, day=d).date(), sch_end_time)
            time_out_dt = TimeHelper.parse_datetime_from_strings(date_str, time_out_str)
            if not time_out_dt:
                return None
            if time_out_dt <= sch_end_dt:
                return 0.0
            delta = time_out_dt - sch_end_dt
            return round(delta.total_seconds() / 3600.0, 2)
        except Exception:
            return None
