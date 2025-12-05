from datetime import datetime
import config


class EmployeeManager:
    def __init__(self, db_conn):
        self.conn = db_conn

    def get_all_employees(self):
        cursor = self.conn.cursor()
        employees = cursor.execute("SELECT id, name, position, department, salary FROM employees ORDER BY id").fetchall()
        cursor.close()
        return employees

    def get_employee_by_id(self, employee_id):
        cursor = self.conn.cursor()
        employee = cursor.execute("SELECT id, name, position, department, salary FROM employees WHERE id=?", (employee_id,)).fetchone()
        cursor.close()
        return employee

    def get_employee_name(self, employee_id):
        cursor = self.conn.cursor()
        result = cursor.execute("SELECT name FROM employees WHERE id=?", (employee_id,)).fetchone()
        cursor.close()
        return result[0] if result else None

    def employee_exists(self, employee_id):
        cursor = self.conn.cursor()
        result = cursor.execute("SELECT 1 FROM employees WHERE id=?", (employee_id,)).fetchone()
        cursor.close()
        return result is not None

    def add_employee(self, emp_id, name, position, department, salary):
        cursor = self.conn.cursor()

        if position in config.POSITION_QUOTAS:
            count = cursor.execute("SELECT COUNT(*) FROM employees WHERE position=?", (position,)).fetchone()[0]
            if count >= config.POSITION_QUOTAS[position]:
                cursor.close()
                return False, f"Maximum for {position} is {config.POSITION_QUOTAS[position]}."

        try:
            cursor.execute("INSERT INTO employees VALUES (?, ?, ?, ?, ?)",
                           (emp_id, name, position, department, salary))
            self.conn.commit()
            cursor.close()
            return True, f"Employee {emp_id} ({name}) added successfully."
        except Exception:
            cursor.close()
            return False, f"Employee ID {emp_id} already exists or cannot be added."

    def update_employee(self, emp_id, name, position, department, salary):
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE employees SET name=?, position=?, department=?, salary=? WHERE id=?
            """, (name, position, department, salary, emp_id))
            self.conn.commit()
            cursor.close()
            return True, f"Employee {emp_id} details updated successfully."
        except Exception as e:
            cursor.close()
            return False, f"An unexpected error occurred during update: {e}"

    def delete_employee(self, emp_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM leaves WHERE employee_id=?", (emp_id,))
            cursor.execute("DELETE FROM attendance WHERE employee_id=?", (emp_id,))
            cursor.execute("DELETE FROM payroll WHERE employee_id=?", (emp_id,))
            cursor.execute("DELETE FROM loans WHERE employee_id=?", (emp_id,))
            cursor.execute("DELETE FROM employees WHERE id=?", (emp_id,))
            self.conn.commit()
            cursor.close()
            return True, f"Employee {emp_id} deleted."
        except Exception as e:
            cursor.close()
            return False, f"Deletion failed: {e}"

    def time_in(self, employee_id):
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        time_now = datetime.now().strftime('%H:%M:%S')

        existing = cursor.execute(
            "SELECT time_in FROM attendance WHERE employee_id=? AND date=?",
            (employee_id, today)
        ).fetchone()

        if existing and existing[0]:
            cursor.close()
            return False, f"Already clocked in today at {existing[0]}."

        try:
            cursor.execute("""
                INSERT INTO attendance (employee_id, date, time_in, time_out)
                VALUES (?, ?, ?, NULL)
                ON CONFLICT(employee_id, date) DO UPDATE SET time_in=?
            """, (employee_id, today, time_now, time_now))
            self.conn.commit()
            cursor.close()
            return True, f"Clocked in at {time_now}."
        except Exception as e:
            cursor.close()
            return False, f"Clock in failed: {e}"

    def time_out(self, employee_id):
        cursor = self.conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        time_now = datetime.now().strftime('%H:%M:%S')

        existing = cursor.execute(
            "SELECT time_in, time_out FROM attendance WHERE employee_id=? AND date=?",
            (employee_id, today)
        ).fetchone()

        if not existing or not existing[0]:
            cursor.close()
            return False, "You must clock in before clocking out."

        if existing[1]:
            cursor.close()
            return False, f"Already clocked out today at {existing[1]}."

        try:
            cursor.execute("""
                UPDATE attendance SET time_out=? WHERE employee_id=? AND date=?
            """, (time_now, employee_id, today))
            self.conn.commit()
            cursor.close()
            return True, f"Clocked out at {time_now}."
        except Exception as e:
            cursor.close()
            return False, f"Clock out failed: {e}"
