
# 💰 Expense Manager (Python + Tkinter + SQLite)

A clean, efficient and fully functional **expense management desktop application** built with Python.  
It allows users to record expenses, filter them, delete entries, view totals, and export data to CSV files.

Designed as a professional-grade project for a developer portfolio.

---

## 🚀 Features

- Add expenses with:
  - Date
  - Category
  - Description
  - Amount
- Dynamic filters:
  - Year
  - Month
  - Category
- Real-time summary:
  - Total expenses
  - Total amount
- Full searchable table (Tkinter Treeview)
- Delete selected expense
- Export current filtered view to CSV
- Data stored locally using SQLite (`expenses.db`)
- Clean and simple user interface

---

## 🛠 Requirements

- Python 3.x  
- No external libraries required (uses only the Python standard library)

---

## ▶️ How to Run

In the folder containing the file:

```bash
python expense_app.py
```

The application will automatically create `expenses.db` on first run.

---

## 📁 Project Structure

```
ExpenseManager/
│── expense_app.py
│── README.md
└── expenses.db    (auto-created)
```

---

## 📤 Exporting Data

You can export filtered expenses to CSV using:

**Buttons → "Export to CSV"**

Choose a filename and the file will be saved with all current rows.

---

## 📄 Data Storage

All data is stored in:

```
expenses.db
```

This file is generated automatically and can be safely moved with the app.

---

## 👨‍💻 Author

Created by **Fabricio Cardozo**  
Built as part of a professional Python portfolio.

---

## 📝 License

MIT License – free to use and modify.
