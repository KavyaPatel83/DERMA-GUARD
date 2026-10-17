"""website/scheduling.py — appointment slot generation."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List

from src.services import db

OPEN_DAYS = {0, 1, 2, 3, 4}        # Mon-Fri
MORNING = range(9, 13)             # 09:00-12:30
AFTERNOON = range(14, 17)          # 14:00-16:30
HORIZON_DAYS = 14


def free_slots(doctor_id: int, days: int = HORIZON_DAYS) -> List[str]:
    taken = {r["slot"] for r in db.all_(
        "SELECT slot FROM appointments WHERE doctor_id=? AND status IN ('booked','confirmed')", (doctor_id,))}
    now = datetime.now() + timedelta(hours=2)
    out: List[str] = []
    for d in range(0, days + 1):
        day = date.today() + timedelta(days=d)
        if day.weekday() not in OPEN_DAYS:
            continue
        for hour in list(MORNING) + list(AFTERNOON):
            for minute in (0, 30):
                dt = datetime(day.year, day.month, day.day, hour, minute)
                if dt < now:
                    continue
                s = dt.strftime("%Y-%m-%dT%H:%M")
                if s not in taken:
                    out.append(s)
    return out


def doctors(department: str | None = None) -> List[Dict]:
    sql = "SELECT id,name,department,specialty,bio FROM users WHERE role='doctor' AND active=1"
    args: tuple = ()
    if department:
        sql += " AND department = ?"
        args = (department,)
    return db.all_(sql + " ORDER BY name", args)


def valid_slot(s: str) -> bool:
    try:
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M")
    except ValueError:
        return False
    return dt.weekday() in OPEN_DAYS and dt.minute in (0, 30) and (dt.hour in MORNING or dt.hour in AFTERNOON) and dt > datetime.now()
