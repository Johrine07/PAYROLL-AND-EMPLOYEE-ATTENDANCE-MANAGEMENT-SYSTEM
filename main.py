import config
import database
import payroll
import employee
import leave_management
import loan_management
import app
import time_utils as time_module 
import schedule 


def main():
    application = app.EmployeeApp()
    application.mainloop()


if __name__ == "__main__":
    main()