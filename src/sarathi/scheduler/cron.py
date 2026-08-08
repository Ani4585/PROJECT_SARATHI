from datetime import datetime, timedelta, timezone
from typing import Optional, Set

class CronExpression:
    """Parses standard 5-field or extended 6-field cron expressions."""

    def __init__(self, expression: str, tz: timezone = timezone.utc):
        self.expression = expression.strip()
        self.tz = tz
        self.fields = self.expression.split()
        if len(self.fields) == 5:
            self.fields.insert(0, "0")
        elif len(self.fields) != 6:
            raise ValueError(f"Invalid cron expression: '{expression}'. Expected 5 or 6 fields.")

        self.seconds = self._parse_field(self.fields[0], 0, 59)
        self.minutes = self._parse_field(self.fields[1], 0, 59)
        self.hours = self._parse_field(self.fields[2], 0, 23)
        self.days_of_month = self._parse_field(self.fields[3], 1, 31)
        self.months = self._parse_field(self.fields[4], 1, 12)
        self.days_of_week = self._parse_field(self.fields[5], 0, 6)

    def _parse_field(self, field: str, min_val: int, max_val: int) -> Set[int]:
        values = set()
        for part in field.split(','):
            if part == '*':
                values.update(range(min_val, max_val + 1))
            elif '/' in part:
                expr, step_str = part.split('/')
                step = int(step_str)
                if expr == '*':
                    start, end = min_val, max_val
                elif '-' in expr:
                    start, end = map(int, expr.split('-'))
                else:
                    start, end = int(expr), max_val
                values.update(range(start, end + 1, step))
            elif '-' in part:
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))
        return values

    def next_fire_time(self, from_time: Optional[datetime] = None) -> datetime:
        dt = (from_time or datetime.now(self.tz)).astimezone(self.tz) + timedelta(seconds=1)
        dt = dt.replace(microsecond=0)

        for _ in range(366 * 24 * 60 * 60):
            if dt.month not in self.months:
                dt += timedelta(days=1)
                dt = dt.replace(hour=0, minute=0, second=0)
                continue
            if dt.day not in self.days_of_month:
                dt += timedelta(days=1)
                dt = dt.replace(hour=0, minute=0, second=0)
                continue
            py_weekday = (dt.weekday() + 1) % 7
            if py_weekday not in self.days_of_week:
                dt += timedelta(days=1)
                dt = dt.replace(hour=0, minute=0, second=0)
                continue
            if dt.hour not in self.hours:
                dt += timedelta(hours=1)
                dt = dt.replace(minute=0, second=0)
                continue
            if dt.minute not in self.minutes:
                dt += timedelta(minutes=1)
                dt = dt.replace(second=0)
                continue
            if dt.second not in self.seconds:
                dt += timedelta(seconds=1)
                continue
            return dt
        raise TimeoutError("Unable to compute next schedule trigger time.")