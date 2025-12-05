from datetime import date, timedelta


class LeaveManager:
    def __init__(self, db_conn):
        self.conn = db_conn

    def get_all_leave_requests(self):
        cursor = self.conn.cursor()
        requests = cursor.execute("""
            SELECT l.id, l.employee_id, e.name, l.date, l.leave_type, l.status
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            ORDER BY l.date DESC, l.status ASC
        """).fetchall()
        cursor.close()
        return requests

    def approve_leave(self, leave_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE leaves SET status='Approved' WHERE id=?", (leave_id,))
        self.conn.commit()
        cursor.close()

    def reject_leave(self, leave_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE leaves SET status='Rejected' WHERE id=?", (leave_id,))
        self.conn.commit()
        cursor.close()

    def delete_leave(self, leave_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM leaves WHERE id=?", (leave_id,))
        self.conn.commit()
        cursor.close()

    def submit_leave_request(self, employee_id, leave_date_str, leave_type):
        cursor = self.conn.cursor()
        
        leave_type_map = {
            'Sick Leave': 'SL',
            'Vacation Leave': 'VL',
            'Vacation Leave (Half Day)': 'VLH'
        }
        lt_code = leave_type_map.get(leave_type, 'SL')

        try:
            leave_date = date.fromisoformat(leave_date_str)
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD."

        if leave_date.weekday() >= 5:
            return False, "Cannot request leave on a weekend."

        start_of_week = leave_date - timedelta(days=leave_date.weekday())
        end_of_week = start_of_week + timedelta(days=4)

        existing = cursor.execute("""
            SELECT leave_type, status FROM leaves
            WHERE employee_id=? AND date BETWEEN ? AND ? AND status IN ('Pending','Approved')
        """, (employee_id, start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d'))).fetchall()

        existing_days = 0.0
        for elt, est in existing:
            if elt == 'VLH':
                existing_days += 0.5
            else:
                existing_days += 1.0

        new_leave_days = 0.5 if lt_code == 'VLH' else 1.0

        if existing_days + new_leave_days > 1:
            return False, f"You can only request up to 1 day of leave per week. Already requested: {existing_days} day(s)."

        try:
            cursor.execute("""
                INSERT INTO leaves (employee_id, date, leave_type, status)
                VALUES (?, ?, ?, 'Pending')
            """, (employee_id, leave_date_str, lt_code))
            self.conn.commit()
            cursor.close()
            return True, f"Leave request for {leave_date_str} submitted successfully."
        except Exception as e:
            cursor.close()
            return False, f"Failed to submit leave request: {e}"
