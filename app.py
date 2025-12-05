import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from datetime import date

import config
import database
import payroll
import employee
import leave_management
import loan_management
from time_utils import TimeHelper
import attendance


class EmployeeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Employee Management System (Payroll & Attendance)")
        self.geometry("1000x700")
        self.db = database.AppDB(config.DB_NAME)
        self.payroll_system = payroll.PayrollSystem(self.db.conn)
        self.employee_manager = employee.EmployeeManager(self.db.conn)
        self.leave_manager = leave_management.LeaveManager(self.db.conn)
        self.loan_manager = loan_management.LoanManager(self.db.conn)
        self._setup_styles()
        self.user_id = None
        self.show_login_page()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='white')
        style.configure('TButton', font=('Arial', 10, 'bold'), padding=10, background='lightgray', foreground='black')
        style.map('TButton', background=[('active', 'gray')])
        style.configure('TLabel', font=('Arial', 10), background='white', foreground='black')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='black', background='white')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='black', background='lightgray')
        style.configure('Bw.TLabelframe', background='white', foreground='black')
        style.configure('Bw.TLabelframe.Label', background='white', foreground='black', font=('Arial', 12, 'bold'))

    def _label(self, parent, text, style='TLabel', font=None, background=None, foreground=None, **pack_opts):
        label_kwargs = {'text': text, 'style': style}
        if font: label_kwargs['font'] = font
        if background: label_kwargs['background'] = background
        if foreground: label_kwargs['foreground'] = foreground
        lbl = ttk.Label(parent, **label_kwargs)
        if pack_opts: lbl.pack(**pack_opts)
        return lbl

    def _combo(self, parent, var, values, width=30, state='readonly', **pack_opts):
        combo = ttk.Combobox(parent, textvariable=var, values=values, state=state, width=width)
        if pack_opts: combo.pack(**pack_opts)
        return combo

    def _button(self, parent, text, cmd, **pack_opts):
        btn = ttk.Button(parent, text=text, command=cmd)
        if pack_opts: btn.pack(**pack_opts)
        return btn

    def _entry(self, parent, width=30, default='', show=None, **pack_opts):
        entry = ttk.Entry(parent, width=width)
        if show: entry.config(show=show)
        if default: entry.insert(0, default)
        if pack_opts: entry.pack(**pack_opts)
        return entry

    def _treeview(self, parent, cols, col_widths=None, col_anchors=None, **pack_opts):
        tree = ttk.Treeview(parent, columns=cols, show='headings')
        for i, col in enumerate(cols):
            tree.heading(col, text=col.replace('_', ' ').title())
            width = col_widths.get(col, 100) if col_widths else 100
            anchor = col_anchors.get(col, 'center') if col_anchors else 'center'
            tree.column(col, width=width, anchor=anchor)
        if pack_opts: tree.pack(**pack_opts)
        return tree

    def _msg(self, msg_type, title, text):
        """Helper for messagebox calls."""
        getattr(messagebox, msg_type.lower())(title, text) if msg_type != 'confirm_yes_no' else messagebox.askyesno(title, text)
        
    def _show_msg(self, msg_type, title, text):
        """Generic message display."""
        if msg_type == 'error': messagebox.showerror(title, text)
        elif msg_type == 'info': messagebox.showinfo(title, text)
        elif msg_type == 'warning': messagebox.showwarning(title, text)
    
    def _confirm(self, title, text):
        """Generic confirmation dialog."""
        return messagebox.askyesno(title, text)

    def _clear_tree(self, tree):
        """Clear all items from treeview."""
        for item in tree.get_children(): tree.delete(item)
    
    def _load_tree_data(self, tree, data, tag_index=None):
        """Generic tree loader with optional tagging."""
        self._clear_tree(tree)
        for row in data:
            tag = row[tag_index].lower() if tag_index else None
            tree.insert('', tk.END, values=row, tags=(tag,) if tag else ())
    
    def _validate_salary(self, salary_str):
        """Validate and return salary or None if invalid."""
        try: return float(salary_str)
        except ValueError: messagebox.showerror("Input Error", "Salary must be a valid number."); return None
    
    def _validate_loan_amount(self, amount_str):
        """Validate and return loan amount or None if invalid."""
        try:
            amt = float(amount_str.strip())
            if amt <= 0: raise ValueError("Amount must be positive")
            return amt
        except ValueError: messagebox.showerror("Input Error", "Please enter a valid loan amount."); return None
    
    def _setup_request_tab(self, tab, title, manager, cols, col_widths, actions, tag_index):
        """Generic tab setup for Leave/Loan requests."""
        self._label(tab, title, style='Header.TLabel', fill='x', pady=10)
        tree = self._treeview(tab, cols, col_widths, expand=True, fill='both', pady=5)
        frame = ttk.Frame(tab)
        frame.pack(pady=10)
        for btn_text, cmd in actions: self._button(frame, btn_text, cmd, side='left', padx=10)
        for status in ['pending', 'approved', 'rejected']:
            colors = {'pending': '#ffeb99', 'approved': '#ccffcc', 'rejected': '#ffcccc'}
            fg = 'darkred' if status == 'rejected' else 'black'
            tree.tag_configure(status, background=colors[status], foreground=fg)
        return tree

    def _logout(self):
        self.user_id = None
        self.show_login_page()

    def show_login_page(self):
        for widget in self.winfo_children():
            widget.destroy()
        login_frame = ttk.Frame(self, padding="20 20 20 20")
        login_frame.pack(expand=True, fill='both')
        self._label(login_frame, "Payroll and Attendance Management System", style='Title.TLabel', pady=20)
        self._label(login_frame, "Admin Code:", pady=5)
        self.admin_code_entry = self._entry(login_frame, width=30, show='*', pady=5)
        self._button(login_frame, "Admin Login", self.admin_login, pady=10)
        ttk.Separator(login_frame, orient='horizontal').pack(fill='x', pady=20)
        self._label(login_frame, "Employee ID: (e.g., EMP001)", pady=5)
        self.employee_id_entry = self._entry(login_frame, width=30, pady=5)
        self._button(login_frame, "Employee Time Clock", self.employee_login, pady=10)

    def admin_login(self):
        code = self.admin_code_entry.get()
        if code == config.ADMIN_CODE:
            self.show_admin_interface()
        else:
            messagebox.showerror("Login Failed", "Invalid Admin Code.")
            self.admin_code_entry.delete(0, tk.END)

    def employee_login(self):
        employee_id = self.employee_id_entry.get().upper().strip()
        if self.employee_manager.employee_exists(employee_id):
            self.user_id = employee_id
            self.show_employee_interface()
        else:
            messagebox.showerror("Login Failed", "Invalid Employee ID.")

    def show_admin_interface(self):
        for widget in self.winfo_children():
            widget.destroy()

        admin_frame = ttk.Frame(self, padding="10")
        admin_frame.pack(expand=True, fill='both')

        top_bar = ttk.Frame(admin_frame)
        top_bar.pack(fill='x')
        ttk.Label(top_bar, text="Admin Dashboard", style='Title.TLabel').pack(side='left', pady=10, padx=10)
        ttk.Button(top_bar, text="Logout", command=self._logout).pack(side='right', pady=10, padx=10)

        notebook = ttk.Notebook(admin_frame)
        notebook.pack(expand=True, fill='both', pady=10)

        self.payroll_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.payroll_tab, text='Payroll & Deductions')
        self._setup_payroll_tab()

        self.attendance_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.attendance_tab, text='Attendance & Absences')
        self._setup_attendance_tab()

        self.schedule_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.schedule_tab, text='Schedules & Shifts')
        self._setup_schedule_tab()

        self.employee_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.employee_tab, text='Employee Data')
        self._setup_employee_tab()

        self.leave_management_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.leave_management_tab, text='Leave Management')
        self._setup_leave_tab()

        self.loan_management_tab = ttk.Frame(notebook, padding="10")
        notebook.add(self.loan_management_tab, text='Loan Management')
        self._setup_loan_tab()

    def _setup_payroll_tab(self):
        select_frame = ttk.Frame(self.payroll_tab, padding="10", style='Header.TLabel')
        select_frame.pack(fill='x', pady=5)
        self._label(select_frame, "Search Name:", side='left', padx=5)
        self.payroll_search_entry = self._entry(select_frame, width=20, side='left', padx=5)
        self.payroll_search_entry.bind('<KeyRelease>', self._filter_payroll_employees)
        employees = self.employee_manager.get_all_employees()
        self.payroll_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.payroll_employee_var = tk.StringVar(self.payroll_tab)
        self.payroll_employee_combo = self._combo(select_frame, self.payroll_employee_var, self.payroll_employees, side='left', padx=10)
        if self.payroll_employees: self.payroll_employee_var.set(self.payroll_employees[0])
        self._button(select_frame, "Refresh Employees", self._refresh_payroll_employees, side='left', padx=10)
        cur_m, cur_y = datetime.date.today().month, datetime.date.today().year
        self.payroll_month_var = tk.StringVar(self.payroll_tab, value=str(cur_m))
        self.payroll_year_var = tk.StringVar(self.payroll_tab, value=str(cur_y))
        self.payroll_period_var = tk.StringVar(self.payroll_tab, value="1")
        self._label(select_frame, "Month:", side='left', padx=(20, 5))
        self._combo(select_frame, self.payroll_month_var, [str(i) for i in range(1, 13)], width=5, side='left', padx=5)
        self._label(select_frame, "Year:", side='left', padx=(10, 5))
        self._combo(select_frame, self.payroll_year_var, [str(cur_y - 1), str(cur_y), str(cur_y + 1)], width=7, side='left', padx=5)
        self._label(select_frame, "Period:", side='left', padx=(10, 5))
        self._combo(select_frame, self.payroll_period_var, ["1", "2"], width=5, side='left', padx=5)
        self._button(select_frame, "Generate Payroll", self._generate_payroll, side='left', padx=15)
        self._button(select_frame, "Generate All Payroll", self._generate_all_payroll, side='left', padx=5)
        self.payroll_text = tk.Text(self.payroll_tab, wrap='word', font=('Consolas', 10), height=25)
        self.payroll_text.pack(expand=True, fill='both', pady=10)

    def _filter_payroll_employees(self, event=None):
        search_term = self.payroll_search_entry.get().lower()
        filtered = [e for e in self.payroll_employees if search_term in e.lower()]
        self.payroll_employee_combo['values'] = filtered
        if filtered:
            self.payroll_employee_var.set(filtered[0])
        else:
            self.payroll_employee_var.set("")

    def _refresh_payroll_employees(self):
        employees = self.employee_manager.get_all_employees()
        self.payroll_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.payroll_employee_combo['values'] = self.payroll_employees
        if self.payroll_employees:
            self.payroll_employee_var.set(self.payroll_employees[0])
        else:
            self.payroll_employee_var.set("")

    def _generate_payroll(self):
        self.payroll_text.delete('1.0', tk.END)
        selected_emp = self.payroll_employee_var.get()
        if not selected_emp:
            self.payroll_text.insert(tk.END, "No employee selected.\n")
            return

        emp_id = selected_emp.split(' - ')[0]
        month = int(self.payroll_month_var.get())
        year = int(self.payroll_year_var.get())
        period = int(self.payroll_period_var.get())

        report, error = self.payroll_system.calculate_pay(emp_id, month, year, period)
        if error:
            self.payroll_text.insert(tk.END, f"Error: {error}\n")
            return

        output = f"""
{'='*80}
{'PAYROLL REPORT':^80}
{'='*80}
Employee ID: {emp_id:<20} | Period: {report['month']} - {report['period_label']}
{'='*80}

{' SALARY INFORMATION ':-^80}
{'Monthly Salary':<35} : PHP {report['monthly_salary']:>20,.2f}
{'Daily Rate':<35} : PHP {report['daily_rate']:>20,.2f}
{'Hourly Rate':<35} : PHP {report['hourly_rate']:>20,.2f}

{' ATTENDANCE ':-^80}
{'Days Present (Worked)':<35} : {report['days_present']:>20.2f}
{'Approved Leave Days':<35} : {report['approved_leaves_days']:>20.2f}
{'Days Absent':<35} : {report['days_absent']:>20.2f}
{'Overtime Hours':<35} : {report['total_overtime_hours']:>20.2f}
{'Tardiness (minutes)':<35} : {report['total_tardiness_minutes']:>20.2f}
{'Undertime (minutes)':<35} : {report['total_undertime_minutes']:>20.2f}

{' EARNINGS ':-^80}
{'Base Pay':<35} : PHP {report['base_pay']:>20,.2f}
{'Overtime Pay':<35} : PHP {report['overtime_pay']:>20,.2f}
{'-'*80}
{'GROSS PAY':<35} : PHP {report['gross_pay']:>20,.2f}

{' DEDUCTIONS ':-^80}
{'SSS':<35} : PHP {report['sss']:>20,.2f}
{'Pag-IBIG':<35} : PHP {report['pagibig']:>20,.2f}
{'PhilHealth':<35} : PHP {report['philhealth']:>20,.2f}
{'Income Tax':<35} : PHP {report['tax']:>20,.2f}
{'Absence Deduction':<35} : PHP {report['absence_deduction']:>20,.2f}
{'Tardiness Deduction':<35} : PHP {report['tardiness_deduction']:>20,.2f}
{'Undertime Deduction':<35} : PHP {report['undertime_deduction']:>20,.2f}
{'Loan Deduction':<35} : PHP {report['loan_deduction']:>20,.2f}
{'-'*80}
{'TOTAL DEDUCTIONS':<35} : PHP {report['total_deductions']:>20,.2f}

{'='*80}
{'NET PAY':<35} : PHP {report['net_pay']:>20,.2f}
{'='*80}
"""
        self.payroll_text.insert(tk.END, output)

    def _setup_attendance_tab(self):
        select_frame = ttk.Frame(self.attendance_tab, padding="10", style='Header.TLabel')
        select_frame.pack(fill='x', pady=5)
        self._label(select_frame, "View Attendance for:", side='left', padx=5)
        employees = self.employee_manager.get_all_employees()
        self.att_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.att_employee_var = tk.StringVar(self.attendance_tab)
        self.att_employee_combo = self._combo(select_frame, self.att_employee_var, self.att_employees, side='left', padx=10)
        if self.att_employees: self.att_employee_var.set(self.att_employees[0])
        self._button(select_frame, "Refresh Employees", self._refresh_attendance_employees, side='left', padx=10)
        cur_m, cur_y = datetime.date.today().month, datetime.date.today().year
        self.att_month_var = tk.StringVar(self.attendance_tab, value=str(cur_m))
        self.att_year_var = tk.StringVar(self.attendance_tab, value=str(cur_y))
        self._label(select_frame, "Month:", side='left', padx=(20, 5))
        self._combo(select_frame, self.att_month_var, [str(i) for i in range(1, 13)], width=5, side='left', padx=5)
        self._label(select_frame, "Year:", side='left', padx=(10, 5))
        self._combo(select_frame, self.att_year_var, [str(cur_y - 1), str(cur_y), str(cur_y + 1)], width=7, side='left', padx=5)
        self._button(select_frame, "View Attendance", self._view_attendance, side='left', padx=15)
        admin_frame = ttk.LabelFrame(select_frame, text="Admin Controls", padding="6")
        admin_frame.pack(side='right', padx=5)
        ttk.Label(admin_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky='w', padx=2, pady=2)
        self.att_date_entry = ttk.Entry(admin_frame, width=12)
        self.att_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        self.att_date_entry.grid(row=0, column=1, sticky='w', padx=2, pady=2)
        ttk.Label(admin_frame, text="Time In (HH:MM[:SS]):").grid(row=1, column=0, sticky='w', padx=2, pady=2)
        self.att_time_in_entry = ttk.Entry(admin_frame, width=10)
        self.att_time_in_entry.grid(row=1, column=1, sticky='w', padx=2, pady=2)
        ttk.Label(admin_frame, text="Time Out (HH:MM[:SS]):").grid(row=2, column=0, sticky='w', padx=2, pady=2)
        self.att_time_out_entry = ttk.Entry(admin_frame, width=10)
        self.att_time_out_entry.grid(row=2, column=1, sticky='w', padx=2, pady=2)
        ttk.Button(admin_frame, text="Set Time", command=self._set_attendance_time).grid(row=3, column=0, columnspan=2, pady=(6,2))
        cols = ('date', 'time_in', 'time_out', 'overtime', 'status')
        self.att_tree = self._treeview(self.attendance_tab, cols, {'date': 100, 'time_in': 100, 'time_out': 100, 'overtime': 100, 'status': 150}, expand=True, fill='both', pady=10)
        self.att_tree.tag_configure('present', background='#ccffcc')
        self.att_tree.tag_configure('absent', background='#ffcccc')
        self.att_tree.tag_configure('leave', background='#ffffcc')
        self.att_summary_label = self._label(self.attendance_tab, "", style='Header.TLabel', fill='x', pady=5)

    def _refresh_attendance_employees(self):
        employees = self.employee_manager.get_all_employees()
        self.att_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.att_employee_combo['values'] = self.att_employees
        if self.att_employees:
            self.att_employee_var.set(self.att_employees[0])
        else:
            self.att_employee_var.set("")

    def _view_attendance(self):
        for i in self.att_tree.get_children():
            self.att_tree.delete(i)

        selected_emp = self.att_employee_var.get()
        if not selected_emp:
            self.att_summary_label.config(text="No employee selected.", foreground='red')
            return

        emp_id = selected_emp.split(' - ')[0]
        month = int(self.att_month_var.get())
        year = int(self.att_year_var.get())

        rows, summary = attendance.get_attendance_report(self.db.conn, self.payroll_system, emp_id, month, year)
        if isinstance(summary, dict) and summary.get('error'):
            self.att_summary_label.config(text=f"Error: {summary.get('error')}", foreground='red')
            return

        for r in rows:
            overtime_display = "-" if r['overtime'] is None else f"{r['overtime']:.2f}"
            tag = 'present' if r['status'].startswith('Present') else ('leave' if r['status'].startswith('On Leave') else 'absent')
            self.att_tree.insert('', tk.END, values=(r['date'], r['time_in'], r['time_out'], overtime_display, r['status']), tags=(tag,))

        self.att_summary_label.config(
            text=f"Summary: Present: {summary['days_present']}, Absent: {summary['days_absent']}, Total Workdays: {summary['total_workdays']}",
            foreground='black'
        )

    def _set_attendance_time(self):
        selected_emp = self.att_employee_var.get()
        if not selected_emp:
            messagebox.showwarning("Selection Error", "No employee selected.")
            return

        emp_id = selected_emp.split(' - ')[0]
        date_str = self.att_date_entry.get().strip()
        time_in = self.att_time_in_entry.get().strip() or None
        time_out = self.att_time_out_entry.get().strip() or None

        # Validate date/time format using TimeHelper
        if not TimeHelper.valid_date(date_str):
            messagebox.showerror("Input Error", "Date must be in YYYY-MM-DD format.")
            return

        if not TimeHelper.valid_time(time_in) or not TimeHelper.valid_time(time_out):
            messagebox.showerror("Input Error", "Time must be HH:MM or HH:MM:SS (24-hour).")
            return

        try:
            cursor = self.db.conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO attendance (employee_id, date, time_in, time_out) VALUES (?, ?, ?, ?)", (emp_id, date_str, time_in, time_out))
            self.db.conn.commit()
            cursor.close()
            messagebox.showinfo("Success", f"Attendance updated for {emp_id} on {date_str}.")

            try:
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                sel_month = int(self.att_month_var.get())
                sel_year = int(self.att_year_var.get())
                if dt.month != sel_month or dt.year != sel_year:
                    self.att_month_var.set(str(dt.month))
                    self.att_year_var.set(str(dt.year))
            except Exception:
                pass

            # Refresh view for the selected employee/month
            self._view_attendance()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update attendance: {e}")

    def _setup_schedule_tab(self):
        select_frame = ttk.Frame(self.schedule_tab, padding="10", style='Header.TLabel')
        select_frame.pack(fill='x', pady=5)
        self._label(select_frame, "View Schedule for:", side='left', padx=5)
        employees = self.employee_manager.get_all_employees()
        self.sched_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.sched_employee_var = tk.StringVar(self.schedule_tab)
        self.sched_employee_combo = self._combo(select_frame, self.sched_employee_var, self.sched_employees, side='left', padx=10)
        if self.sched_employees: self.sched_employee_var.set(self.sched_employees[0])
        self._button(select_frame, "Refresh Employees", self._refresh_schedule_employees, side='left', padx=10)
        cur_m, cur_y = datetime.date.today().month, datetime.date.today().year
        self.sched_month_var = tk.StringVar(self.schedule_tab, value=str(cur_m))
        self.sched_year_var = tk.StringVar(self.schedule_tab, value=str(cur_y))
        self._label(select_frame, "Month:", side='left', padx=(20, 5))
        self._combo(select_frame, self.sched_month_var, [str(i) for i in range(1, 13)], width=5, side='left', padx=5)
        self._label(select_frame, "Year:", side='left', padx=(10, 5))
        self._combo(select_frame, self.sched_year_var, [str(cur_y - 1), str(cur_y), str(cur_y + 1)], width=7, side='left', padx=5)
        self._button(select_frame, "Generate Schedule", self._generate_schedule_view, side='left', padx=15)
        self._button(select_frame, "Open Calendar View", self._open_calendar_view, side='left', padx=5)
        cols = ('date', 'day', 'shift_details')
        self.schedule_tree = self._treeview(self.schedule_tab, cols, {'date': 100, 'day': 80, 'shift_details': 200}, col_anchors={'shift_details': 'w'}, expand=True, fill='both', pady=10)
        self.schedule_tree.tag_configure('work_day', background='#ccffcc')
        self.schedule_tree.tag_configure('rest_day', background='#e0e0e0')
        self.schedule_info_label = self._label(self.schedule_tab, "", style='Header.TLabel', fill='x', pady=5)

    def _refresh_schedule_employees(self):
        employees = self.employee_manager.get_all_employees()
        self.sched_employees = [f"{eid} - {name}" for eid, name, _, _, _ in employees]
        self.sched_employee_combo['values'] = self.sched_employees
        if self.sched_employees:
            self.sched_employee_var.set(self.sched_employees[0])
        else:
            self.sched_employee_var.set("")

    def _generate_schedule_view(self):
        # Delegate to ScheduleGenerator in schedule.py
        try:
            from schedule import ScheduleGenerator
        except Exception:
            self.schedule_info_label.config(text="Schedule module not available.", foreground='red')
            return

        selected_emp = self.sched_employee_var.get()
        month = int(self.sched_month_var.get())
        year = int(self.sched_year_var.get())

        ScheduleGenerator.generate_and_populate(
            self.schedule_tree,
            self.schedule_info_label,
            selected_emp,
            month,
            year,
            self.payroll_system,
        )

    def _generate_all_payroll(self):
        # produce overview for all employees for selected month/year/period
        self.payroll_text.delete('1.0', tk.END)
        month = int(self.payroll_month_var.get())
        year = int(self.payroll_year_var.get())
        period = int(self.payroll_period_var.get())

        employees = self.employee_manager.get_all_employees()
        if not employees:
            self.payroll_text.insert(tk.END, "No employees found.\n")
            return

        # header
        title = f"Payroll Overview - {date(year, month, 1).strftime('%B %Y')} - Period {period}"
        header = f"{title:^100}\n"
        header += "="*100 + "\n"
        header += f"{'ID':<12} | {'Name':<25} | {'Gross Pay':>18} | {'Total Deductions':>18} | {'Net Pay':>18}\n"
        header += "-"*100 + "\n"
        self.payroll_text.insert(tk.END, header)

        grand_totals = {'gross': 0.0, 'deductions': 0.0, 'net': 0.0}
        for eid, name, _, _, _ in employees:
            report, error = self.payroll_system.calculate_pay(eid, month, year, period)
            if error or not report:
                line = f"{eid:<12} | {name:<25} | Error: {error or 'N/A'}\n"
                self.payroll_text.insert(tk.END, line)
                continue
            gross = report.get('gross_pay', 0.0)
            deductions = report.get('total_deductions', 0.0)
            net = report.get('net_pay', 0.0)
            grand_totals['gross'] += gross
            grand_totals['deductions'] += deductions
            grand_totals['net'] += net
            line = f"{eid:<12} | {name:<25} | PHP {gross:>14,.2f} | PHP {deductions:>14,.2f} | PHP {net:>14,.2f}\n"
            self.payroll_text.insert(tk.END, line)

        footer = "-"*100 + "\n"
        footer += f"{'TOTAL':<12} | {'':<25} | PHP {grand_totals['gross']:>14,.2f} | PHP {grand_totals['deductions']:>14,.2f} | PHP {grand_totals['net']:>14,.2f}\n"
        footer += "="*100 + "\n"
        self.payroll_text.insert(tk.END, footer)

    def _open_calendar_view(self):
        try:
            from tkcalendar import Calendar
        except Exception as e:
            messagebox.showinfo("Calendar Not Installed", "tkcalendar is not installed. Install it to enable calendar view.\n\npip install tkcalendar")
            return

        selected_emp = self.sched_employee_var.get()
        if not selected_emp:
            messagebox.showerror("Error", "No employee selected.")
            return
        
        try:
            emp_id = selected_emp.split(' - ')[0]
            month = int(self.sched_month_var.get())
            year = int(self.sched_year_var.get())

            schedule, _ = self.payroll_system.get_employee_schedule(emp_id, month, year)

            win = tk.Toplevel(self)
            win.title(f"Calendar View - {selected_emp}")
            win.geometry("600x500")

            cal = Calendar(win, selectmode='day', year=year, month=month, day=1)
            cal.pack(pady=10, fill='both', expand=True)

            if schedule:
                for dstr, info in schedule.items():
                    try:
                        if info.startswith("Work Day"):
                            y, m, dd = map(int, dstr.split("-"))
                            cal.calevent_create(date(y, m, dd), info, 'work')
                    except Exception:
                        pass
            
            cal.tag_config('work', background='lightgreen', foreground='black')
        except Exception as e:
            messagebox.showerror("Calendar Error", f"Failed to open calendar: {str(e)}")

    def _setup_employee_tab(self):
        input_frame = ttk.LabelFrame(self.employee_tab, text="Employee Details (Add New or Edit Selected)", padding="10")
        input_frame.pack(fill='x', pady=10)
        fields = ['ID (e.g., EMP001):', 'Name:', 'Position:', 'Department:', 'Monthly Salary:']
        self.emp_entries = {}
        for i, field in enumerate(fields):
            ttk.Label(input_frame, text=field).grid(row=i // 2, column=(i % 2) * 2, padx=10, pady=5, sticky='w')
            self.emp_entries[field] = ttk.Entry(input_frame, width=30)
            self.emp_entries[field].grid(row=i // 2, column=(i % 2) * 2 + 1, padx=10, pady=5, sticky='w')
        button_frame = ttk.Frame(self.employee_tab)
        button_frame.pack(fill='x', pady=10)
        self._button(button_frame, "Add New Employee", self._add_employee, side='left', padx=10)
        self.edit_button = self._button(button_frame, "Save Edits", self._edit_employee, side='left', padx=10)
        self.edit_button.config(state='disabled')
        self.cancel_edit_button = self._button(button_frame, "Cancel Edit", self._cancel_edit, side='left', padx=10)
        self.cancel_edit_button.config(state='disabled')
        self.delete_button = self._button(button_frame, "Delete Selected", self._delete_employee, side='left', padx=10)
        self.delete_button.config(state='disabled')
        self._label(self.employee_tab, "All Employees (Click to Edit or Delete)", style='Header.TLabel', fill='x', pady=10)
        cols = ('id', 'name', 'position', 'department', 'salary')
        col_widths = {'id': 100, 'name': 150, 'position': 150, 'department': 150, 'salary': 100}
        self.employee_tree = self._treeview(self.employee_tab, cols, col_widths, expand=True, fill='both', pady=5)
        self.employee_tree.bind("<<TreeviewSelect>>", self._load_employee_for_edit)
        self._load_all_employees()

    def _load_all_employees(self):
        self._clear_tree(self.employee_tree)
        for emp in self.employee_manager.get_all_employees():
            self.employee_tree.insert('', tk.END, values=(emp[0], emp[1], emp[2], emp[3], f"PHP {emp[4]:,.2f}"))

    def _cancel_edit(self):
        for entry in self.emp_entries.values():
            entry.delete(0, tk.END)
        self.emp_entries['ID (e.g., EMP001):'].config(state='normal')
        self.edit_button.config(state='disabled')
        self.cancel_edit_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.employee_tree.selection_remove(self.employee_tree.selection())

    def _load_employee_for_edit(self, event):
        selected_item = self.employee_tree.focus()
        if not selected_item:
            return
        values = self.employee_tree.item(selected_item, 'values')
        if not values:
            return

        for entry in self.emp_entries.values():
            entry.delete(0, tk.END)

        id_field = self.emp_entries['ID (e.g., EMP001):']
        id_field.insert(0, values[0])
        id_field.config(state='disabled')

        self.emp_entries['Name:'].insert(0, values[1])
        self.emp_entries['Position:'].insert(0, values[2])
        self.emp_entries['Department:'].insert(0, values[3])
        salary_str = values[4].replace("PHP ", "").replace(",", "")
        self.emp_entries['Monthly Salary:'].insert(0, salary_str)

        self.edit_button.config(state='normal')
        self.cancel_edit_button.config(state='normal')
        self.delete_button.config(state='normal')

    def _add_employee(self):
        data = {k: v.get() for k, v in self.emp_entries.items()}
        emp_id, name, position, department = data['ID (e.g., EMP001):'].strip().upper(), data['Name:'], data['Position:'], data['Department:']
        salary = self._validate_salary(data['Monthly Salary:'])
        if not salary or not all([emp_id, name, position, department]): messagebox.showerror("Input Error", "All fields are required."); return
        success, msg = self.employee_manager.add_employee(emp_id, name, position, department, salary)
        if success: messagebox.showinfo("Success", msg); self._load_all_employees(); self._cancel_edit()
        else: messagebox.showerror("Error", msg)

    def _edit_employee(self):
        emp_id = self.emp_entries['ID (e.g., EMP001):'].get().strip().upper()
        if not emp_id: messagebox.showerror("Error", "No Employee ID selected for edit."); return
        data = {k: v.get() for k, v in self.emp_entries.items()}
        name, position, department = data['Name:'], data['Position:'], data['Department:']
        salary = self._validate_salary(data['Monthly Salary:'])
        if not salary or not all([name, position, department]): messagebox.showerror("Input Error", "All fields are required."); return
        success, msg = self.employee_manager.update_employee(emp_id, name, position, department, salary)
        if success: messagebox.showinfo("Success", msg); self._load_all_employees(); self._cancel_edit()
        else: messagebox.showerror("Error", msg)

    def _delete_employee(self):
        self.emp_entries['ID (e.g., EMP001):'].config(state='normal')
        emp_id = self.emp_entries['ID (e.g., EMP001):'].get().strip().upper()
        if self.edit_button.cget('state') == 'normal': self.emp_entries['ID (e.g., EMP001):'].config(state='disabled')
        if not emp_id: messagebox.showerror("Error", "Please select an employee from the list to delete."); return
        if not self._confirm("Confirm Deletion", f"Delete employee {emp_id} and ALL their records?"): return
        success, msg = self.employee_manager.delete_employee(emp_id)
        if success: messagebox.showinfo("Success", msg); self._load_all_employees(); self._cancel_edit()
        else: messagebox.showerror("Error", msg)

    def _setup_leave_tab(self):
        cols = ('id', 'employee_id', 'name', 'date', 'type', 'status')
        col_widths = {'id': 50, 'employee_id': 100, 'name': 150, 'date': 100, 'type': 80, 'status': 100}
        actions = [("Approve Selected Leave", lambda: self._approve_reject_leave('Approved')), 
                   ("Reject Selected Leave", lambda: self._approve_reject_leave('Rejected')), 
                   ("Delete Selected Leave", self._delete_leave), ("Refresh List", self._load_leave_requests)]
        self.leave_tree = self._setup_request_tab(self.leave_management_tab, "Leave Requests (All Statuses)", 
                                                   self.leave_manager, cols, col_widths, actions, 5)
        self._load_leave_requests()

    def _load_leave_requests(self):
        requests = self.leave_manager.get_all_leave_requests()
        self._load_tree_data(self.leave_tree, requests, tag_index=5)

    def _approve_reject_leave(self, status):
        selected_item = self.leave_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select a leave request."); return
        values = self.leave_tree.item(selected_item, 'values')
        leave_date = datetime.datetime.strptime(values[3], '%Y-%m-%d').date()
        if leave_date < date.today(): messagebox.showerror("Invalid Action", "Cannot modify leave requests for past dates."); return
        if self._confirm("Confirm Action", f"Set leave ID {values[0]} to '{status}'?"):
            (self.leave_manager.approve_leave if status == 'Approved' else self.leave_manager.reject_leave)(values[0])
            self._load_leave_requests()

    def _delete_leave(self):
        selected_item = self.leave_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Select a leave to delete."); return
        values = self.leave_tree.item(selected_item, 'values')
        leave_date = datetime.datetime.strptime(values[3], '%Y-%m-%d').date()
        if leave_date < date.today(): messagebox.showerror("Invalid Action", "Cannot delete leave requests for past dates."); return
        if self._confirm("Confirm Deletion", f"Delete leave ID {values[0]}?"): 
            self.leave_manager.delete_leave(values[0]); self._load_leave_requests()

    def _setup_loan_tab(self):
        cols = ('id', 'employee_id', 'name', 'amount', 'remaining', 'date', 'status')
        col_widths = {'id': 50, 'employee_id': 100, 'name': 150, 'amount': 100, 'remaining': 100, 'date': 120, 'status': 100}
        actions = [("Approve Selected Loan", lambda: self._approve_reject_loan('Approved')), 
                   ("Reject Selected Loan", lambda: self._approve_reject_loan('Rejected')), 
                   ("Refresh List", self._load_loans)]
        self.loan_tree = self._setup_request_tab(self.loan_management_tab, "Loan Requests", 
                                                  self.loan_manager, cols, col_widths, actions, 6)
        self._load_loans()

    def _load_loans(self):
        loans = self.loan_manager.get_all_loans()
        self._load_tree_data(self.loan_tree, loans, tag_index=6)

    def _approve_reject_loan(self, status):
        selected_item = self.loan_tree.focus()
        if not selected_item: messagebox.showwarning("Selection Error", "Please select a loan request."); return
        values = self.loan_tree.item(selected_item, 'values')
        if self._confirm("Confirm Action", f"Set loan ID {values[0]} to '{status}'?"):
            (self.loan_manager.approve_loan if status == "Approved" else self.loan_manager.reject_loan)(values[0])
            self._load_loans()

    def show_employee_interface(self):
        for widget in self.winfo_children():
            widget.destroy()
        emp_frame = ttk.Frame(self, padding="50 50 50 50")
        emp_frame.pack(expand=True, fill='both')
        emp_name = self.employee_manager.get_employee_name(self.user_id)
        top_bar = ttk.Frame(emp_frame)
        top_bar.pack(fill='x')
        self._label(top_bar, f"Welcome, {emp_name}", style='Title.TLabel', side='left', pady=10)
        self._label(top_bar, f"Employee ID: {self.user_id}", font=('Arial', 12), background='white', foreground='black', side='left', padx=20)
        self._button(top_bar, "Logout", self._logout, side='right', padx=10)
        clock_frame = ttk.LabelFrame(emp_frame, text="Time Clock", padding="20", style='Bw.TLabelframe')
        clock_frame.pack(pady=10, fill='x')
        self.status_label = ttk.Label(clock_frame, text="Ready to Clock In/Out.", font=('Arial', 14, 'bold'), foreground='black', background='white')
        self.status_label.pack(pady=10)
        button_frame = ttk.Frame(clock_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="TIME IN", command=self._time_in, style='TButton').grid(row=0, column=0, padx=20, ipadx=20, ipady=10)
        ttk.Button(button_frame, text="TIME OUT", command=self._time_out, style='TButton').grid(row=0, column=1, padx=20, ipadx=20, ipady=10)
        leave_frame = ttk.LabelFrame(emp_frame, text="Request Leave", padding="20", style='Bw.TLabelframe')
        leave_frame.pack(pady=20, fill='x')
        ttk.Label(leave_frame, text="Date for Leave (YYYY-MM-DD):", background='white', foreground='black').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.leave_date_entry = ttk.Entry(leave_frame, width=15)
        self.leave_date_entry.insert(0, date.today().strftime('%Y-%m-%d'))
        self.leave_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Label(leave_frame, text="Leave Type:", background='white', foreground='black').grid(row=0, column=2, padx=15, pady=5, sticky='w')
        self.leave_type_var = tk.StringVar(leave_frame, value='Sick Leave')
        ttk.Combobox(leave_frame, textvariable=self.leave_type_var, values=['Sick Leave', 'Vacation Leave', 'Vacation Leave (Half Day)'], state='readonly', width=20).grid(row=0, column=3, padx=5, pady=5, sticky='w')
        ttk.Button(leave_frame, text="Submit Leave Request", command=self._submit_leave_request, style='TButton').grid(row=0, column=4, padx=15, sticky='e')
        loan_frame = ttk.LabelFrame(emp_frame, text="Request Loan", padding="20", style='Bw.TLabelframe')
        loan_frame.pack(pady=20, fill='x')
        ttk.Label(loan_frame, text="Loan Amount (PHP):", background='white', foreground='black').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.loan_amount_entry = ttk.Entry(loan_frame, width=15)
        self.loan_amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Button(loan_frame, text="Submit Loan Request", command=self._submit_loan_request, style='TButton').grid(row=0, column=2, padx=15, sticky='e')

    def _time_in(self):
        success, message = self.employee_manager.time_in(self.user_id)
        if success:
            self.status_label.config(text=message, foreground='green')
        else:
            self.status_label.config(text=message, foreground='red')

    def _time_out(self):
        success, message = self.employee_manager.time_out(self.user_id)
        if success:
            self.status_label.config(text=message, foreground='green')
        else:
            self.status_label.config(text=message, foreground='red')

    def _submit_leave_request(self):
        leave_date_str = self.leave_date_entry.get().strip()
        leave_type = self.leave_type_var.get()

        success, message = self.leave_manager.submit_leave_request(self.user_id, leave_date_str, leave_type)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def _submit_loan_request(self):
        try:
            amount = float(self.loan_amount_entry.get().strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid loan amount.")
            return

        success, message = self.loan_manager.submit_loan_request(self.user_id, amount)
        if success:
            messagebox.showinfo("Success", message)
            self.loan_amount_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)