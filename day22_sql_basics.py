import sqlite3

conn = sqlite3.connect("company.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS employees")
cursor.execute("DROP TABLE IF EXISTS departments")

cursor.execute("""
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary INTEGER,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

departments = [
    (1, "Engineering"),
    (2, "Sales"),
    (3, "HR")
]
cursor.executemany("INSERT INTO departments VALUES (?, ?)", departments)

employees = [
    (1, "Ali", 90000, 1),
    (2, "Sara", 75000, 1),
    (3, "Ahmed", 60000, 2),
    (4, "Fatima", 65000, 2),
    (5, "Bilal", 50000, 3),
]
cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", employees)

conn.commit()
conn.close()
print("Database created with sample data.")