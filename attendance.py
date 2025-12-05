from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional

from time_utils import TimeHelper


def get_attendance_report(db_conn, payroll_system, emp_id: str, month: int, year: int) -> Tuple[List[Dict], Dict]:
    """Return attendance rows and summary for the given employee/month/year.

    rows: list of dicts with keys: date (YYYY-MM-DD), time_in, time_out, overtime (float or None), status
    summary: dict with keys: total_workdays, days_present, days_absent

    This is a pure data/function implementation without GUI calls.
    """
    cursor = db_conn.cursor()
    start_date = date(year, month, 1)
    # compute end of month safely
    end_date = (start_date.replace(day=28) + timedelta(days=4))
    end_date = end_date - timedelta(days=end_date.day)

    # get schedule from payroll system (may return schedule dict or error string)
    schedule, total_workdays = payroll_system.get_employee_schedule(emp_id, month, year)
    if isinstance(schedule, str):
        return [], {"error": schedule}

    attendance_records = cursor.execute(
        """
        SELECT date, time_in, time_out FROM attendance
        WHERE employee_id=? AND date BETWEEN ? AND ?
        ORDER BY date
        """,
        (emp_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    ).fetchall()

    att_map = {r[0]: (r[1], r[2]) for r in attendance_records}

    leaves = cursor.execute(
        """
        SELECT date, leave_type FROM leaves
        WHERE employee_id=? AND status='Approved' AND date BETWEEN ? AND ?
        """,
        (emp_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    ).fetchall()
    leave_map = {l[0]: l[1] for l in leaves}

    # lookup employee position/department to determine scheduled end time
    emp_row = cursor.execute("SELECT position, department FROM employees WHERE id= ?", (emp_id,)).fetchone()
    emp_pos = emp_row[0] if emp_row else None
    emp_dept = emp_row[1] if emp_row and len(emp_row) > 1 else None

    rows = []
    days_present = 0.0
    days_absent = 0.0

    for date_str, day_info in schedule.items():
        if "Rest Day" in day_info:
            continue

        time_in = att_map.get(date_str, (None, None))[0] or "-"
        time_out = att_map.get(date_str, (None, None))[1] or "-"

        overtime_val: Optional[float] = None
        if time_out != "-":
            try:
                sch_end = None
                if emp_pos and emp_pos.startswith("Security Guard") and emp_dept == "Security":
                    if emp_pos.endswith("A"):
                        shift = payroll_system.GUARD_SHIFTS[0]
                    elif emp_pos.endswith("B"):
                        shift = payroll_system.GUARD_SHIFTS[1]
                    else:
                        shift = payroll_system.GUARD_SHIFTS[2]
                    sch_end = shift.get('end')
                else:
                    shift_def = payroll_system.POSITION_SHIFTS.get(emp_pos, {"start": datetime.time(8, 0), "end": datetime.time(16, 0)})
                    sch_end = shift_def.get('end')

                if sch_end:
                    ot = TimeHelper.calculate_overtime_hours(sch_end, date_str, time_out)
                    overtime_val = ot
            except Exception:
                overtime_val = None

        if date_str in leave_map:
            status = f"On Leave ({leave_map[date_str]})"
            days_present += 0.5 if leave_map[date_str] == 'VLH' else 1
        elif time_in != "-" and time_out != "-":
            status = "Present"
            days_present += 1
        else:
            status = "Absent"
            days_absent += 1

        rows.append({
            "date": date_str,
            "time_in": time_in,
            "time_out": time_out,
            "overtime": overtime_val,
            "status": status,
        })

    cursor.close()
    summary = {
        "total_workdays": total_workdays,
        "days_present": days_present,
        "days_absent": days_absent,
    }
    return rows, summary
