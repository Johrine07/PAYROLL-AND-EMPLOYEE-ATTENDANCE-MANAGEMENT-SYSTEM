💻 PAYROLL AND EMPLOYEE ATTENDANCE MANAGEMENT SYSTEM 💻

Project Overview 

This system is a Payroll and Employee Attendance System designed to automate and simplify how an organization manages its workforce. 
It replaces manual tracking with a centralized software solution that records attendance, computes salaries, manages employee information, 
handles deductions, and supports administrative decisions through a clean Graphical User Interface (GUI). 
It is built primarily using Python and utilizes Tkinter for the user interface and SQLite3 for persistent internal data storage. 
Key Features 

• Automated Payroll Computation: Calculates net pay based on attendance, absences, tardiness, overtime, and leaves. 

• Centralized Employee Records: Securely stores employee IDs, names, positions, salary rates, and departments. 

• Attendance Tracking: Records daily time-in and time-out used for payroll computation. 

• Deduction Management: Automatically handles mandatory government deductions (SSS, PhilHealth, Pag-IBIG, Tax) and applies deductions for loans, tardiness, and undertime. 
• Leave and Loan Management: Allows tracking and approval of employee leave requests and loan balances. 

• User-Friendly GUI: Provides an intuitive interface for staff and administrators (built with Tkinter).

------------------------------------------------------------------------------------------------------------
Access and Login

• The application has two main login modes: Admin and Employee Time Clock.

Admin Access

• Admin Code (Default): admin0107 
• Functionality: Allows access to the Admin Dashboard, which includes:
- Employee Data management (Add, Edit, Delete)
- Payroll Calculation
- Attendance and Absence tracking
- Leave and Loan management
  
Employee Time Clock

• Requirement: Requires a valid Employee ID (e.g., EMP001). 

• Functionality: Allows the specific employee to: Clock IN and Clock OUT for the day. 

• Applying for loans and leave

-----------------------------------------------------------------------------------------------------------

💻 USERS OPENS THE PROGRAMS 💻 

The program starts the Tkinter GUI, which allows the user to access modules.

Employee Registration Through the GUI, the user can add:

• Employee ID, Name, Position, Department, Monthly Salary

Attendance Recording The user enters: 

• Employee ID, Date, Time In, Time Out, 

Payroll Computation When generating payroll, the system reads: 

• Employee Information, Attendance Records, Leave Records, and Loan Records 

The system computes: Earnings:

• Base pay for the days worked
• Overtime pays 
• Leave pay 

Deductions: 

• Absence deduction
• Tardiness deduction 
• Undertime deduction
• Government contributions 
• Loan repayment 

The result is: NET PAY = GROSS PAY – TOTAL DEDUCTIONS

It will display Payroll / Pay slips 

The system shows a breakdown how the earnings computated.

-----------------------------------------------------------------------------------------------------------
CONTRIBUTORS 👋

Rhea Johrine K. Cudiamat 

Gelyn C. Reyes 
