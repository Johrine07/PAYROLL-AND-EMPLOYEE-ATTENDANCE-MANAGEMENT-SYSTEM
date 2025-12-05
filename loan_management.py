from datetime import datetime


class LoanManager:
    def __init__(self, db_conn):
        self.conn = db_conn

    def get_all_loans(self):
        cursor = self.conn.cursor()
        loans = cursor.execute("""
            SELECT l.id, l.employee_id, e.name, l.amount, l.remaining_balance, l.date_requested, l.status
            FROM loans l
            JOIN employees e ON l.employee_id = e.id
            ORDER BY l.date_requested DESC
        """).fetchall()
        cursor.close()
        return loans

    def approve_loan(self, loan_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE loans SET status='Approved', remaining_balance=amount WHERE id=?
        """, (loan_id,))
        self.conn.commit()
        cursor.close()

    def reject_loan(self, loan_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE loans SET status='Rejected' WHERE id=?", (loan_id,))
        self.conn.commit()
        cursor.close()

    def submit_loan_request(self, employee_id, amount):
        cursor = self.conn.cursor()

        salary_row = cursor.execute("SELECT salary FROM employees WHERE id=?", (employee_id,)).fetchone()
        if not salary_row:
            cursor.close()
            return False, "Employee not found."

        monthly_salary = salary_row[0]
        max_loan = monthly_salary * 3

        existing_loans = cursor.execute("""
            SELECT SUM(remaining_balance) FROM loans
            WHERE employee_id=? AND status='Approved' AND remaining_balance > 0
        """, (employee_id,)).fetchone()[0] or 0.0

        if existing_loans + amount > max_loan:
            cursor.close()
            return False, f"Total loan amount exceeds 3x monthly salary limit (PHP {max_loan:,.2f})."

        try:
            cursor.execute("""
                INSERT INTO loans (employee_id, amount, remaining_balance, date_requested, status)
                VALUES (?, ?, 0, ?, 'Pending')
            """, (employee_id, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            cursor.close()
            return True, f"Loan request for PHP {amount:,.2f} submitted successfully."
        except Exception as e:
            cursor.close()
            return False, f"Failed to submit loan request: {e}"
