import sys
import sqlite3
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QInputDialog, QFileDialog, QScrollArea, QHBoxLayout, QDateEdit, QLabel
)
from openpyxl import Workbook
from PyQt5.QtCore import (QDate, Qt)
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog


# Database connection settings
DB_NAME = "devpresso_db.sqlite"

class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Devpresso")
        self.setGeometry(100, 100, 400, 200)
        self.setMinimumSize(300, 150)  # Set a minimum size for dynamic resizing

        # Initialize the UI
        self.init_ui()

    def init_ui(self):
        # Main layout with spacing and padding
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Create and add buttons
        self.create_buttons(layout)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Apply stylesheet for styling
        self.apply_styles()

    def create_buttons(self, layout):
        # Button to go to Transactions Window
        transactions_btn = QPushButton("Transactions", self)
        transactions_btn.clicked.connect(self.open_transactions_window)
        layout.addWidget(transactions_btn)

        # Button to go to Drink Menu Window
        drink_menu_btn = QPushButton("Drinks Menu", self)
        drink_menu_btn.clicked.connect(self.open_drink_menu_window)
        layout.addWidget(drink_menu_btn)

    def open_transactions_window(self):
        self.transactions_window = TransactionsWindow()
        self.transactions_window.show()

    def open_drink_menu_window(self):
        self.drink_menu_window = DrinkMenuWindow()
        self.drink_menu_window.show()

    def apply_styles(self):
        # Apply a stylesheet for modern button styling
        self.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px;
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QMainWindow {
                background-color: #f0f0f0;
            }
        """)


from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtCore import Qt

class TransactionsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transactions")
        self.setGeometry(150, 150, 800, 500)
        self.setMinimumSize(600, 400)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Date filter layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Start Date filter
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())  # Set current date by default
        self.start_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("Start Date:"))
        filter_layout.addWidget(self.start_date_edit)

        # End Date filter
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())  # Set current date by default
        self.end_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("End Date:"))
        filter_layout.addWidget(self.end_date_edit)

        # Button to apply filter
        self.filter_btn = QPushButton("Apply Filter")
        self.filter_btn.clicked.connect(self.load_transactions)
        filter_layout.addWidget(self.filter_btn)

        layout.addLayout(filter_layout)

        # Table to display transactions
        self.transactions_table = QTableWidget(0, 10)  # Increased column count for the print button
        self.transactions_table.setHorizontalHeaderLabels(
            ["No", "Date", "Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)", "Paid", "Payment Method", "Print"]
        )
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.setAlternatingRowColors(True)
        layout.addWidget(self.transactions_table)

        # Enable editing and track changes
        self.transactions_table.itemChanged.connect(self.handle_item_changed)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Button to add transaction
        self.add_btn = QPushButton("Add Transaction")
        self.add_btn.clicked.connect(self.add_transaction)
        btn_layout.addWidget(self.add_btn)

        # Button to delete transaction
        self.delete_btn = QPushButton("Delete Transaction")
        self.delete_btn.clicked.connect(self.delete_transaction)
        btn_layout.addWidget(self.delete_btn)

        # Download CSV button
        self.download_csv_btn = QPushButton("Download CSV")
        self.download_csv_btn.clicked.connect(self.download_transactions_csv)
        btn_layout.addWidget(self.download_csv_btn)

        # Download Excel button
        self.download_excel_btn = QPushButton("Download Excel")
        self.download_excel_btn.clicked.connect(self.download_transactions_excel)
        btn_layout.addWidget(self.download_excel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load transactions data
        self.create_table()
        self.load_transactions()  # Initial load without filter

    def create_table(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                drink_type TEXT,
                variant TEXT,
                quantity INTEGER,
                total_price REAL,
                date TEXT,
                paid BOOLEAN DEFAULT 0,  -- New column for paid status
                payment_method TEXT DEFAULT '-' -- New column for payment method
            )
        """)
        connection.commit()
        connection.close()

    def load_transactions(self):
        # Get selected start and end dates
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, date, customer_name, drink_type, variant, quantity, total_price, paid, payment_method 
            FROM transactions
            WHERE date BETWEEN ? AND ?
        """, (start_date, end_date))

        records = cursor.fetchall()
        self.transactions_table.setRowCount(0)

        for row_data in records:
            row_count = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_count)
            for col, data in enumerate(row_data):
                if col == 7:  # Paid column
                    checkbox = QTableWidgetItem()
                    checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    checkbox.setCheckState(Qt.Checked if data else Qt.Unchecked)
                    self.transactions_table.setItem(row_count, col, checkbox)
                elif col == 8:  # Payment Method column
                    combo = QComboBox()
                    combo.addItems(["QRIS", "Cash", "-"])
                    combo.setCurrentText(data)
                    combo.currentIndexChanged.connect(lambda index, r=row_count, c=col: self.handle_payment_method_change(r, c))
                    self.transactions_table.setCellWidget(row_count, col, combo)
                elif col == 5:  # Total Price column (col 5 is total_price)
                    if isinstance(data, (int, float)):
                        formatted_data = f"{int(data):,}".replace(",", ".")
                    else:
                        formatted_data = f"{int(float(data.replace(',', ''))):,}".replace(",", ".")
                    self.transactions_table.setItem(row_count, col, QTableWidgetItem(formatted_data))
                else:
                    self.transactions_table.setItem(row_count, col, QTableWidgetItem(str(data)))

            # Add Print button to the last column of each row
            print_btn = QPushButton("Print")
            print_btn.clicked.connect(lambda _, r=row_count: self.print_transaction(r))
            self.transactions_table.setCellWidget(row_count, 9, print_btn)

        cursor.close()
        connection.close()

    def print_transaction(self, row):
        # Fetch the transaction details from the row
        transaction_id = self.transactions_table.item(row, 0).text()  # ID is in the first column
        transaction_date = self.transactions_table.item(row, 1).text()
        customer_name = self.transactions_table.item(row, 2).text()
        drink_type = self.transactions_table.item(row, 3).text()
        variant = self.transactions_table.item(row, 4).text()
        quantity = self.transactions_table.item(row, 5).text()
        total_price = self.transactions_table.item(row, 6).text()
        paid = "Paid" if self.transactions_table.item(row, 7).checkState() == Qt.Checked else "Unpaid"
        payment_method = self.transactions_table.cellWidget(row, 8).currentText()

        # Prepare the print content
        print_content = f"""
        Transaction ID: {transaction_id}
        Date: {transaction_date}
        Customer Name: {customer_name}
        Drink Type: {drink_type}
        Variant: {variant}
        Quantity: {quantity}
        Total Price: {total_price}
        Paid: {paid}
        Payment Method: {payment_method}
        """

        # Print using QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        print_dialog = QPrintDialog(printer, self)

        if print_dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            painter.begin(printer)
            painter.setFont(QFont("Arial", 12))

            # Print content
            painter.drawText(100, 100, print_content)
            painter.end()

    def handle_item_changed(self, item):
        row = item.row()
        column = item.column()

        column_mapping = {
            "No": "id",
            "Date": "date",
            "Customer Name": "customer_name",
            "Drink Type": "drink_type",
            "Variant": "variant",
            "Quantity": "quantity",
            "Total Price (Rp)": "total_price",
            "Paid": "paid",
            "Payment Method": "payment_method",
        }

        header_text = self.transactions_table.horizontalHeaderItem(column).text()
        column_name = column_mapping.get(header_text)

        if not column_name:
            return

        transaction_id = self.transactions_table.item(row, 0).text()  # ID is in the first column
        new_value = item.text()

        if column_name == "paid":
            new_value = 1 if item.checkState() == Qt.Checked else 0

        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute(f"UPDATE transactions SET {column_name} = ? WHERE id = ?", (new_value, transaction_id))
        connection.commit()
        connection.close()

    def handle_payment_method_change(self, row, column):
        transaction_id = self.transactions_table.item(row, 0).text()
        combo = self.transactions_table.cellWidget(row, column)
        new_payment_method = combo.currentText()

        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("UPDATE transactions SET payment_method = ? WHERE id = ?", (new_payment_method, transaction_id))
        connection.commit()
        connection.close()

    def add_transaction(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        # Ensure the drinks table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drinks (
                drink_type TEXT,
                variant TEXT,
                price REAL
            )
        """)

        # Input customer name
        customer_name, ok0 = QInputDialog.getText(self, "Add Transaction", "Enter Customer Name:")
        if not ok0 or not customer_name.strip():
            cursor.close()
            connection.close()
            return

        # Fetch distinct drink types from the drinks table
        cursor.execute("SELECT DISTINCT drink_type FROM drinks")
        drink_types = [row[0] for row in cursor.fetchall()]
        if not drink_types:
            QMessageBox.warning(self, "No Drinks Available", "Please add drinks to the menu first.")
            cursor.close()
            connection.close()
            return

        drink_type, ok1 = QInputDialog.getItem(self, "Add Transaction", "Select Drink Type:", drink_types, editable=False)
        if not ok1:
            cursor.close()
            connection.close()
            return

        # Fetch variants for the selected drink type
        cursor.execute("SELECT variant, price FROM drinks WHERE drink_type = ?", (drink_type,))
        variants = cursor.fetchall()
        if not variants:
            QMessageBox.warning(self, "No Variants Available", f"No variants found for the drink type '{drink_type}'.")
            cursor.close()
            connection.close()
            return

        variant_options = [f"{variant} - Rp {price:,.0f}" for variant, price in variants]
        selected_variant, ok2 = QInputDialog.getItem(self, "Add Transaction", "Select Variant:", variant_options, editable=False)
        if not ok2:
            cursor.close()
            connection.close()
            return

        variant, price_str = selected_variant.split(" - ")
        price = float(price_str.replace("Rp ", "").replace(",", ""))

        quantity, ok3 = QInputDialog.getInt(self, "Add Transaction", "Enter Quantity:", min=1)
        if not ok3:
            cursor.close()
            connection.close()
            return

        total_price = int(price * quantity)  # Store as integer (no decimals)

        # Get today's date
        transaction_date = QDate.currentDate().toString("yyyy-MM-dd")  # Automatically set the date to today

        # Insert transaction into the database with customer name and the current date
        cursor.execute(
            "INSERT INTO transactions (customer_name, drink_type, variant, quantity, total_price, date) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_name, drink_type, variant, quantity, total_price, transaction_date)
        )

        connection.commit()
        cursor.close()
        connection.close()

        self.load_transactions()  # Reload the transaction list after insertion


    def delete_transaction(self):
        selected_row = self.transactions_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Delete Transaction", "Please select a transaction to delete.")
            return

        # Get the transaction ID (which is in the first column after loading the transactions)
        transaction_id = self.transactions_table.item(selected_row, 0).text()

        # Confirmation dialog
        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the transaction with ID '{transaction_id}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            connection.commit()
            cursor.close()
            connection.close()

            # Refresh the table after deletion (reload the data)
            self.load_transactions()
        
    def get_filtered_dates(self):
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            return start_date, end_date

    def download_transactions_csv(self):
        start_date, end_date = self.get_filtered_dates()

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Transactions", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("""
                SELECT date, customer_name, drink_type, variant, quantity, total_price, 
                    CASE WHEN paid = 1 THEN 'True' ELSE 'False' END as paid, payment_method 
                FROM transactions
                WHERE date BETWEEN ? AND ?
            """, (start_date, end_date))
            records = cursor.fetchall()
            connection.close()

            # Calculating totals for quantity and amount as integers
            total_quantity = sum(int(record[4]) for record in records)  # column 4 is quantity
            total_amount = sum(int(record[5]) for record in records)  # column 5 is total_price
            total_paid_true = sum(1 for record in records if record[6] == 'True')  # Count 'True' values for paid

            # Writing data to CSV file
            with open(file_name, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)", "Paid", "Payment Method"])
                for row in records:
                    formatted_row = list(row)
                    formatted_row[5] = int(formatted_row[5])  # Convert total_price to integer
                    writer.writerow(formatted_row)

                # Add totals row with 'Paid' column count (e.g., 2/3)
                paid_ratio = f"{total_paid_true}/{len(records)}"
                total_row = ["", "", "", "Total", total_quantity, total_amount, paid_ratio, ""]
                writer.writerow(total_row)

            QMessageBox.information(self, "Success", f"Transactions saved to {file_name}")

    def download_transactions_excel(self):
            start_date, end_date = self.get_filtered_dates()

            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Transactions", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
            if file_name:
                connection = sqlite3.connect(DB_NAME)
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT date, customer_name, drink_type, variant, quantity, total_price, 
                        CASE WHEN paid = 1 THEN 'True' ELSE 'False' END as paid, payment_method 
                    FROM transactions
                    WHERE date BETWEEN ? AND ?
                """, (start_date, end_date))
                records = cursor.fetchall()
                connection.close()

                # Calculating totals for quantity and amount as integers
                total_quantity = sum(int(record[4]) for record in records)  # column 4 is quantity
                total_amount = sum(int(record[5]) for record in records)  # column 5 is total_price
                total_paid_true = sum(1 for record in records if record[6] == 'True')  # Count 'True' values for paid

                # Writing data to Excel file
                workbook = Workbook()
                sheet = workbook.active
                sheet.title = "Transactions"
                sheet.append(["Date", "Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)", "Paid", "Payment Method"])

                # Data rows
                for row in records:
                    formatted_row = list(row)
                    formatted_row[5] = int(formatted_row[5])  # Ensure total_price is stored as an integer
                    sheet.append(formatted_row)

                # Total row at the bottom
                paid_ratio = f"{total_paid_true}/{len(records)}"
                total_row = ["", "", "", "Total", total_quantity, total_amount, paid_ratio, ""]
                sheet.append(total_row)

                # Apply formatting for thousands separator
                for row_idx in range(2, len(records) + 3):  # Rows with data and total
                    sheet.cell(row=row_idx, column=6).number_format = '#,##0'  # Format Total Price (Rp)
                sheet.cell(row=len(records) + 3, column=5).number_format = '#,##0'  # Format Total Quantity
                sheet.cell(row=len(records) + 3, column=6).number_format = '#,##0'  # Format Total Amount

                workbook.save(file_name)
                QMessageBox.information(self, "Success", f"Transactions saved to {file_name}")


class DrinkMenuWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drink Menu")
        self.setGeometry(150, 150, 700, 500)  # Increased width and height for better spacing
        self.setMinimumSize(600, 400)  # Allow dynamic resizing

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Scroll area for the drink menu table
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Table to display drink menu
        self.drink_menu_table = QTableWidget(0, 3)
        self.drink_menu_table.setHorizontalHeaderLabels(["Drink Type", "Variant", "Price (Rp)"])
        self.drink_menu_table.horizontalHeader().setStretchLastSection(True)
        self.drink_menu_table.verticalHeader().setVisible(False)
        self.drink_menu_table.setAlternatingRowColors(True)

        # Add table to the scroll area
        scroll_area.setWidget(self.drink_menu_table)
        layout.addWidget(scroll_area)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Button to add drink
        self.add_btn = QPushButton("Add Drink")
        self.add_btn.clicked.connect(self.add_drink)
        btn_layout.addWidget(self.add_btn)

        # Button to delete drink
        self.delete_btn = QPushButton("Delete Drink")
        self.delete_btn.clicked.connect(self.delete_drink)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.load_drinks()


    def load_drinks(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()

        # Ensure the drinks table has the correct columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drinks (
                drink_type TEXT,
                variant TEXT,
                price REAL
            )
        """)

        cursor.execute("SELECT drink_type, variant, price FROM drinks")
        records = cursor.fetchall()
        self.drink_menu_table.setRowCount(0)
        for row_data in records:
            row_count = self.drink_menu_table.rowCount()
            self.drink_menu_table.insertRow(row_count)
            self.drink_menu_table.setItem(row_count, 0, QTableWidgetItem(row_data[0]))
            self.drink_menu_table.setItem(row_count, 1, QTableWidgetItem(row_data[1]))
            self.drink_menu_table.setItem(row_count, 2, QTableWidgetItem(f"Rp {row_data[2]:,.0f}"))
        cursor.close()
        connection.close()

    def add_drink(self):
        drink_type, ok1 = QInputDialog.getText(self, "Add Drink", "Enter Drink Type:")
        if not ok1 or not drink_type.strip():
            return

        variant, ok2 = QInputDialog.getText(self, "Add Drink", "Enter Variant:")
        if not ok2 or not variant.strip():
            return

        price, ok3 = QInputDialog.getDouble(self, "Add Drink", "Enter Price:", min=0)
        if ok3:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO drinks (drink_type, variant, price) VALUES (?, ?, ?)", (drink_type, variant, price))
            connection.commit()
            cursor.close()
            connection.close()
            self.load_drinks()

    def delete_drink(self):
        selected_row = self.drink_menu_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Delete Drink", "Please select a drink to delete.")
            return

        drink_type = self.drink_menu_table.item(selected_row, 0).text()
        variant = self.drink_menu_table.item(selected_row, 1).text()

        # Confirmation dialog
        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the drink '{drink_type} - {variant}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("DELETE FROM drinks WHERE drink_type = ? AND variant = ?", (drink_type, variant))
            connection.commit()
            cursor.close()
            connection.close()

            self.drink_menu_table.removeRow(selected_row)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainMenu()
    main_window.show()
    sys.exit(app.exec_())
