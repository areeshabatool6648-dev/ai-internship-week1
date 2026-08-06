from fastapi import FastAPI, HTTPException
import sqlite3

app = FastAPI()

def get_connection():
    conn = sqlite3.connect("company.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/employees")
def get_employees():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)

@app.post("/employees")
def create_employee(name: str, salary: int, department_id: int):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO employees (name, salary, department_id) VALUES (?, ?, ?)",
        (name, salary, department_id)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "name": name, "salary": salary, "department_id": department_id}

@app.put("/employees/{employee_id}")
def update_employee_salary(employee_id: int, salary: int):
    conn = get_connection()
    result = conn.execute("UPDATE employees SET salary = ? WHERE id = ?", (salary, employee_id))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"id": employee_id, "new_salary": salary}

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    conn = get_connection()
    result = conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": f"Employee {employee_id} deleted"}