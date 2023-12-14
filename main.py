import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import Calendar
from tkcalendar import DateEntry
import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()

# Create an expenses table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        category TEXT,
        amount REAL,
        date DATE
    )
''')
conn.commit()

# Function to add an expense to the database
def add_expense():
    # Retrieve data from input fields
    description = description_entry.get()
    category = category_entry.get()
    amount = amount_entry.get()
    date = date_calendar.get_date()

    try:
        amount = float(amount)
    except ValueError:
        error_label.config(text="Amount must be a valid number.")
        return

    # Check if description and category are provided
    if description and category:
        data = (description, category, amount, date)
        cursor.execute('INSERT INTO expenses (description, category, amount, date) VALUES (?, ?, ?, ?)', data)
        conn.commit()

        update_expense_list()
        clear_entries()
        error_label.config(text="Expense added successfully.")
    else:
        error_label.config(text="Please fill in all the fields.")

# Function to edit an existing expense
def edit_expense():
    # Get the selected expense ID from the list
    selected_item = expense_list.selection()
    if not selected_item:
        return

    selected_expense_id = expense_list.item(selected_item, "values")[4]

    # Create a new window for editing
    edit_window = tk.Toplevel()
    edit_window.title('Edit Expense')

    # Fetch expense data based on its ID
    cursor.execute('SELECT * FROM expenses WHERE id=?', (selected_expense_id,))
    expense_data = cursor.fetchone()

    # Create a Calendar widget for date selection
    date_label = ttk.Label(edit_window, text='Date:')
    date_label.grid(row=3, column=0, padx=5, pady=5)
    date_calendar = Calendar(edit_window, date_pattern='yyyy-mm-dd')
    date_calendar.grid(row=3, column=1, padx=5, pady=5)

    description_label = ttk.Label(edit_window, text='Description:')
    description_label.grid(row=0, column=0, padx=5, pady=5)
    description_entry_edit = ttk.Entry(edit_window)
    description_entry_edit.grid(row=0, column=1, padx=5, pady=5)
    description_entry_edit.insert(0, expense_data[1])

    category_label = ttk.Label(edit_window, text='Category:')
    category_label.grid(row=1, column=0, padx=5, pady=5)
    category_entry_edit = ttk.Entry(edit_window)
    category_entry_edit.grid(row=1, column=1, padx=5, pady=5)
    category_entry_edit.insert(0, expense_data[2])

    amount_label = ttk.Label(edit_window, text='Amount:')
    amount_label.grid(row=2, column=0, padx=5, pady=5)
    amount_entry_edit = ttk.Entry(edit_window)
    amount_entry_edit.grid(row=2, column=1, padx=5, pady=5)
    amount_entry_edit.insert(0, str(expense_data[3]))

    def save_edited_expense():
        new_description = description_entry_edit.get()
        new_category = category_entry_edit.get()
        new_amount = amount_entry_edit.get()
        new_date = date_calendar.get_date()

        if new_description and new_category and new_amount:
            edited_data = (new_description, new_category, float(new_amount), new_date)
            cursor.execute('UPDATE expenses SET description=?, category=?, amount=?, date=? WHERE id=?',
                           (new_description, new_category, float(new_amount), new_date, selected_expense_id))
            conn.commit()

            edit_window.destroy()
            update_expense_list()
        else:
            error_label.config(text="Please fill in all the fields.")

    save_button = ttk.Button(edit_window, text='Save', command=save_edited_expense)
    save_button.grid(row=4, columnspan=2, padx=5, pady=10)

# Function to update the expense list in the UI
def update_expense_list():
    cursor.execute('SELECT * FROM expenses')
    expenses = cursor.fetchall()

    expense_list.delete(*expense_list.get_children())

    # Populate the expense list with database records
    for expense in expenses:
        item_id = expense[0]
        description = expense[1]
        category = expense[2]
        amount = expense[3]
        date = expense[4]
        expense_list.insert('', 'end', values=(description, category, amount, date, item_id))

# Function to clear input fields
def clear_entries():
    description_entry.delete(0, 'end')
    category_entry.delete(0, 'end')
    amount_entry.delete(0, 'end')

# Function to delete the selected expense
def delete_selected_expense():
    selected_item = expense_list.selection()
    if selected_item:
        item_id = expense_list.item(selected_item, "values")[4]
        cursor.execute('DELETE FROM expenses WHERE id=?', (item_id,))
        conn.commit()
        update_expense_list()
        clear_entries()

# Function to generate an expense report
def generate_report():
    start_date = start_date_entry.get_date()
    end_date = end_date_entry.get_date()

    cursor.execute('''
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE date BETWEEN ? AND ?
        GROUP BY category
    ''', (start_date, end_date))

    categories = {row[0]: row[1] for row in cursor.fetchall()}

    # Plot a pie chart based on expense categories
    plt.clf()
    plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
    plt.title('Expense Categories')

    # Create a new FigureCanvasTkAgg instance and display the chart
    canvas = FigureCanvasTkAgg(plt.gcf(), master=report_frame)
    canvas_widget = canvas.get_tk_widget()

    # Use grid geometry manager for the canvas widget
    canvas_widget.grid(row=3, columnspan=2, padx=5, pady=5)

    # Draw the plot
    canvas.draw()

# Create the main application window
app = tk.Tk()
app.title('Expense Tracker')

# Create a notebook-style UI for different sections
notebook = ttk.Notebook(app)
notebook.pack(padx=10, pady=10)

# Add Expense section
expense_frame = ttk.Frame(notebook)
notebook.add(expense_frame, text='Add Expense')

date_label = ttk.Label(expense_frame, text='Date:')
date_label.grid(row=3, column=0, padx=5, pady=5)
date_calendar = Calendar(expense_frame, date_pattern='yyyy-mm-dd')
date_calendar.grid(row=3, column=1, padx=5, pady=5)

description_label = ttk.Label(expense_frame, text='Description:')
description_label.grid(row=0, column=0, padx=5, pady=5)
description_entry = ttk.Entry(expense_frame)
description_entry.grid(row=0, column=1, padx=5, pady=5)

category_label = ttk.Label(expense_frame, text='Category:')
category_label.grid(row=1, column=0, padx=5, pady=5)
category_entry = ttk.Entry(expense_frame)
category_entry.grid(row=1, column=1, padx=5, pady=5)

amount_label = ttk.Label(expense_frame, text='Amount:')
amount_label.grid(row=2, column=0, padx=5, pady=5)
amount_entry = ttk.Entry(expense_frame)
amount_entry.grid(row=2, column=1, padx=5, pady=5)

add_button = ttk.Button(expense_frame, text='Add Expense', command=add_expense)
add_button.grid(row=4, columnspan=2, padx=5, pady=10)

error_label = ttk.Label(expense_frame, text="", foreground="red")
error_label.grid(row=5, columnspan=2, padx=5, pady=10)

list_frame = ttk.Frame(notebook)
notebook.add(list_frame, text='Expense List')

expense_list = ttk.Treeview(list_frame, column=('Description', 'Category', 'Amount', 'Date', 'Item ID'), show='headings')
expense_list.heading('#1', text='Description')
expense_list.heading('#2', text='Category')
expense_list.heading('#3', text='Amount')
expense_list.heading('#4', text='Date')
expense_list.heading('#5', text='Item ID')
expense_list.pack(padx=5, pady=5)

update_expense_list()

edit_button = ttk.Button(list_frame, text='Edit Expense', command=edit_expense)
edit_button.pack(padx=5, pady=10)
delete_button = ttk.Button(list_frame, text='Delete Expense', command=delete_selected_expense)
delete_button.pack(padx=5, pady=10)

report_frame = ttk.Frame(notebook)
notebook.add(report_frame, text='Expense Report')

start_label = ttk.Label(report_frame, text='Start Date:')
start_label.grid(row=0, column=0, padx=5, pady=5)
start_date_entry = DateEntry(report_frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2)
start_date_entry.grid(row=0, column=1, padx=5, pady=5)

end_label = ttk.Label(report_frame, text='End Date:')
end_label.grid(row=1, column=0, padx=5, pady=5)
end_date_entry = DateEntry(report_frame, width=12, background='darkblue',
                           foreground='white', borderwidth=2)
end_date_entry.grid(row=1, column=1, padx=5, pady=5)

generate_report_button = ttk.Button(report_frame, text='Generate Report', command=generate_report)
generate_report_button.grid(row=2, columnspan=2, padx=5, pady=10)

app.mainloop()

conn.close()  # Close the SQLite connection when the program exits