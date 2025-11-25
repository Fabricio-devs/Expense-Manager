import csv
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


DB_FILE = "expenses.db"


class ExpenseRepository:
    """Small SQLite wrapper to store and query expenses."""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def add_expense(self, date_str: str, category: str, description: str, amount: float):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                (date_str, category, description, amount),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_expense(self, expense_id: int):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()
        finally:
            conn.close()

    def fetch_expenses(self, year=None, month=None, category=None):
        """Returns a list of (id, date, category, description, amount)."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, date, category, description, amount FROM expenses WHERE 1=1"
            params = []

            if year and year != "All":
                query += " AND strftime('%Y', date) = ?"
                params.append(str(year))
            if month and month != "All":
                query += " AND strftime('%m', date) = ?"
                params.append(f"{int(month):02d}")
            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY date DESC, id DESC"
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            conn.close()

    def get_summary(self, year=None, month=None, category=None):
        """Returns (count, total_amount) for the current filter."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses WHERE 1=1"
            params = []

            if year and year != "All":
                query += " AND strftime('%Y', date) = ?"
                params.append(str(year))
            if month and month != "All":
                query += " AND strftime('%m', date) = ?"
                params.append(f"{int(month):02d}")
            if category and category != "All":
                query += " AND category = ?"
                params.append(category)

            cur.execute(query, params)
            count, total = cur.fetchone()
            return int(count), float(total)
        finally:
            conn.close()

    def fetch_distinct_categories(self):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT category FROM expenses ORDER BY category")
            return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()


class ExpenseApp(tk.Tk):
    """Main Tkinter application for managing expenses."""

    def __init__(self):
        super().__init__()
        self.title("Expense Manager")
        self.geometry("800x500")
        self.resizable(False, False)

        self.repo = ExpenseRepository()

        self._build_ui()
        self._load_filters()
        self.refresh_table()

    # ---------------------------------------------------------------
    # ----------------------------- UI ------------------------------
    # ---------------------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)
        
        # ------------------------------------------------------------------
        # ------------------------ Add expense form ------------------------
        # ------------------------------------------------------------------
        
        form = ttk.LabelFrame(main, text="Add expense")
        form.pack(fill="x")

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(form, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(form, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=["Food", "Transport", "Housing", "Utilities", "Entertainment", "Health", "Other"],
            width=18,
        )
        self.category_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.category_combo.set("Food")

        ttk.Label(form, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_var = tk.StringVar()
        self.desc_entry = ttk.Entry(form, textvariable=self.desc_var, width=40)
        self.desc_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Label(form, text="Amount:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(form, textvariable=self.amount_var, width=12)
        self.amount_entry.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        add_btn = ttk.Button(form, text="Add", command=self.add_expense)
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        # ---------------------------------------------------------------------------
        # --------------------------------- Filters ---------------------------------
        # ---------------------------------------------------------------------------
        
        filter_frame = ttk.LabelFrame(main, text="Filters")
        filter_frame.pack(fill="x", pady=(10, 0))

        ttk.Label(filter_frame, text="Year:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filter_year = tk.StringVar(value="All")
        self.year_combo = ttk.Combobox(filter_frame, textvariable=self.filter_year, state="readonly", width=8)
        self.year_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(filter_frame, text="Month:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.filter_month = tk.StringVar(value="All")
        self.month_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_month,
            state="readonly",
            width=8,
            values=["All"] + [f"{m:02d}" for m in range(1, 13)],
        )
        self.month_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.filter_category = tk.StringVar(value="All")
        self.category_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_category,
            state="readonly",
            width=15,
        )
        self.category_filter_combo.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        apply_btn = ttk.Button(filter_frame, text="Apply filters", command=self.refresh_table)
        apply_btn.grid(row=0, column=6, padx=10, pady=5)

        # -----------------------------------------------------------
        # -------------------------- Table --------------------------
        # -----------------------------------------------------------
        
        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True, pady=(10, 0))

        # first column will store the DB id (hidden)
        columns = ("id", "date", "category", "description", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("date", width=90, anchor="w")
        self.tree.column("category", width=100, anchor="w")
        self.tree.column("description", width=380, anchor="w")
        self.tree.column("amount", width=90, anchor="e")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ----------------------------------------------------------------------------
        # ------------------------- Bottom actions & summary -------------------------
        # ----------------------------------------------------------------------------
        
        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(10, 0))

        delete_btn = ttk.Button(bottom, text="Delete selected", command=self.delete_selected)
        delete_btn.pack(side="left")

        export_btn = ttk.Button(bottom, text="Export to CSV", command=self.export_csv)
        export_btn.pack(side="left", padx=(10, 0))

        self.summary_label = ttk.Label(bottom, text="0 expenses | Total: 0.00", anchor="e")
        self.summary_label.pack(side="right")
        
    # ---------------------------------------------------------
    # ------------------------ Filters ------------------------
    # ---------------------------------------------------------

    def _load_filters(self):
        conn = sqlite3.connect(DB_FILE)
        years = set()
        try:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT strftime('%Y', date) FROM expenses")
            years = {row[0] for row in cur.fetchall() if row[0] is not None}
        finally:
            conn.close()

        year_values = ["All"] + sorted(years)
        self.year_combo["values"] = year_values
        self.year_combo.set("All")

        categories = self.repo.fetch_distinct_categories()
        cat_values = ["All"] + categories
        self.category_filter_combo["values"] = cat_values
        self.category_filter_combo.set("All")

    # --------------------------------------------------
    # ------------------ CRUD actions ------------------
    #--------------------------------------------------    

    def add_expense(self):
        date_str = self.date_var.get().strip()
        category = self.category_var.get().strip() or "Other"
        description = self.desc_var.get().strip()
        amount_str = self.amount_var.get().strip()

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Please use format YYYY-MM-DD.")
            return

        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showerror("Invalid amount", "Amount must be a number.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero.")
            return

        self.repo.add_expense(date_str, category, description, amount)
        self.desc_var.set("")
        self.amount_var.set("")

        self._load_filters()
        self.refresh_table()

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Please select an expense to delete.")
            return

        if not messagebox.askyesno("Confirm deletion", "Delete selected expense?"):
            return

        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        db_id = int(values[0])

        self.repo.delete_expense(db_id)
        self.refresh_table()

    # ---------------------------------------------------------
    # ------------------------ Listing ------------------------
    # ---------------------------------------------------------

    def _get_current_filters(self):
        year = self.filter_year.get()
        month = self.filter_month.get()
        category = self.filter_category.get()
        return year, month, category

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        year, month, category = self._get_current_filters()
        rows = self.repo.fetch_expenses(year=year, month=month, category=category)

        for db_id, date_str, cat, desc, amount in rows:
            self.tree.insert("", "end", values=(db_id, date_str, cat, desc, f"{amount:.2f}"))

        count, total = self.repo.get_summary(year=year, month=month, category=category)
        self.summary_label.config(text=f"{count} expenses | Total: {total:.2f}")

    # ----------------------------------------------------
    # ---------------------- Export ----------------------
    # ----------------------------------------------------

    def export_csv(self):
        year, month, category = self._get_current_filters()
        rows = self.repo.fetch_expenses(year=year, month=month, category=category)

        if not rows:
            messagebox.showinfo("No data", "No expenses to export with current filters.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save CSV file",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "date", "category", "description", "amount"])
                for row in rows:
                    writer.writerow(row)
        except Exception as e:
            messagebox.showerror("Error", f"Could not export file:\n{e}")
            return

        messagebox.showinfo("Export complete", "Expenses exported successfully.")


if __name__ == "__main__":
    app = ExpenseApp()
    app.mainloop()
