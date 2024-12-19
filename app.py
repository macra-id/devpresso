import sys
import sqlite3
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QDialog, QMessageBox, QInputDialog, QFileDialog, QScrollArea, QHBoxLayout, QDateEdit
)
from openpyxl import Workbook
from PyQt5.QtCore import QDate

# Database connection settings
DB_NAME = "devpresso_db.sqlite"

class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Menu")
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
        transactions_btn = QPushButton("Go to Transactions", self)
        transactions_btn.clicked.connect(self.open_transactions_window)
        layout.addWidget(transactions_btn)

        # Button to go to Drink Menu Window
        drink_menu_btn = QPushButton("Go to Drink Menu", self)
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


class TransactionsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transactions")
        self.setGeometry(150, 150, 800, 500)  # Increased width and height for better spacing
        self.setMinimumSize(600, 400)  # Allow dynamic resizing

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Table to display transactions
        self.transactions_table = QTableWidget(0, 7)
        self.transactions_table.setHorizontalHeaderLabels(
            ["No","Date","Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)"]
        )
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.setAlternatingRowColors(True)
        layout.addWidget(self.transactions_table)

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

        # Button to download transactions as CSV
        self.download_csv_btn = QPushButton("Download CSV")
        self.download_csv_btn.clicked.connect(self.download_transactions_csv)
        btn_layout.addWidget(self.download_csv_btn)

        # Button to download transactions as Excel
        self.download_excel_btn = QPushButton("Download Excel")
        self.download_excel_btn.clicked.connect(self.download_transactions_excel)
        btn_layout.addWidget(self.download_excel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load transactions data
        self.create_table()
        self.load_transactions()

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
                date TEXT  -- New column for storing the transaction date
            )
        """)
        connection.commit()
        connection.close()

    def load_transactions(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        cursor.execute("SELECT id, date, customer_name, drink_type, variant, quantity, total_price FROM transactions")
        records = cursor.fetchall()
        self.transactions_table.setRowCount(0)
        for row_data in records:
            row_count = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_count)
            for col, data in enumerate(row_data):
                self.transactions_table.setItem(row_count, col, QTableWidgetItem(str(data)))
        cursor.close()
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

        total_price = price * quantity

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
        self.load_transactions()

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


        
    def download_transactions_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Transactions", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if file_name:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("SELECT date, customer_name, drink_type, variant, quantity, total_price FROM transactions")
            records = cursor.fetchall()
            connection.close()

            # Calculating totals for quantity and amount
            total_quantity = sum(record[4] for record in records)  # column 4 is quantity
            total_amount = sum(record[5] for record in records)  # column 5 is total_price

            # Writing data to CSV file
            with open(file_name, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)"])  # Date first
                for row in records:
                    writer.writerow(row)  # Write each row of data
                writer.writerow(["", "", "", "Total", total_quantity, total_amount])  # Total row

            QMessageBox.information(self, "Success", f"Transactions saved to {file_name}")

    def download_transactions_excel(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Transactions", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("SELECT date, customer_name, drink_type, variant, quantity, total_price FROM transactions")
            records = cursor.fetchall()
            connection.close()

            # Calculating totals for quantity and amount
            total_quantity = sum(record[4] for record in records)  # column 4 is quantity
            total_amount = sum(record[5] for record in records)  # column 5 is total_price

            # Writing data to Excel file
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Transactions"
            sheet.append(["Date", "Customer Name", "Drink Type", "Variant", "Quantity", "Total Price (Rp)"])  # Date first
            for row in records:
                sheet.append(row)  # Write each row of data
            sheet.append(["", "", "", "Total", total_quantity, total_amount])  # Total row

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
