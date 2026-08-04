import sqlite3

conn = sqlite3.connect("company.db")
cursor = conn.cursor()

# Purani tables hatao agar pehle se hain (dobara chalane ke liye)
cursor.execute("DROP TABLE IF EXISTS employees")
cursor.execute("DROP TABLE IF EXISTS departments")

# Table 1: departments
cursor.execute("""
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

# Table 2: employees (department se linked)
cursor.execute("""
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary INTEGER,
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
)
""")

# Data daalo
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
print("Database created with sample data.\n")

# ---- Query 1: Simple SELECT with WHERE ----
print("=== Query 1: Employees earning more than 60000 ===")
cursor.execute("SELECT name, salary FROM employees WHERE salary > 60000")
for row in cursor.fetchall():
    print(row)

# ---- Query 2: JOIN ----
print("\n=== Query 2: Employee names with their department names (JOIN) ===")
cursor.execute("""
SELECT employees.name, departments.name
FROM employees
JOIN departments ON employees.department_id = departments.id
""")
for row in cursor.fetchall():
    print(row)

# ---- Query 3: GROUP BY ----
print("\n=== Query 3: Average salary per department (GROUP BY) ===")
cursor.execute("""
SELECT departments.name, AVG(employees.salary) as avg_salary, COUNT(employees.id) as num_employees
FROM employees
JOIN departments ON employees.department_id = departments.id
GROUP BY departments.name
""")
for row in cursor.fetchall():
    print(row)

conn.close()