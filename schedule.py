import datetime
from datetime import date

class ScheduleGenerator:
    """Encapsulates schedule generation and population of a Treeview and label.

    Methods are static so they can be used from UI code without instantiating.
    """

    @staticmethod
    def generate_and_populate(schedule_tree, schedule_info_label, selected_emp, month, year, payroll_system):

        for i in schedule_tree.get_children():
            schedule_tree.delete(i)

        if not selected_emp:
            schedule_info_label.config(text="No employee selected.", foreground='red')
            return

        emp_id = selected_emp.split(' - ')[0]

        schedule, total_workdays = payroll_system.get_employee_schedule(emp_id, month, year)
        if isinstance(schedule, str):
            schedule_info_label.config(text=f"Error: {schedule}", foreground='red')
            return

        for date_str, details in schedule.items():
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                day_name = date_obj.strftime('%a')
            except Exception:
                day_name = ''

            tag = 'work_day' if details.startswith("Work Day") or "Shift" in details else 'rest_day'
            schedule_tree.insert('', 'end', values=(date_str, day_name, details), tags=(tag,))

        schedule_info_label.config(
            text=f"Schedule generated for {selected_emp} in {date(year, month, 1).strftime('%B %Y')}. Total expected workdays: {total_workdays}.",
            foreground='black'
        )
