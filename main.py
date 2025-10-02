from fastmcp import FastMCP
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS Expenses(
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Date TEXT NOT NULL,
                    Amount REAL NOT NULL,
                    Category TEXT NOT NULL,
                    SubCategory TEXT DEFAULT '',
                    Note TEXT DEFAULT ''
                ) 
        """)

init_db()

@mcp.tool
def add_expense(Date, Amount, Category, SubCategory="", Note=""):
    '''Add a new expense entry to the database.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO Expenses(Date, Amount, Category, SubCategory, Note) VALUES (?,?,?,?,?)",
            (Date, Amount, Category, SubCategory, Note)
        )
        return {"status": "ok", "ID": cur.lastrowid}
    
@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT ID, Date, Amount, Category, SubCategory, Note
            FROM Expenses
            WHERE Date BETWEEN ? AND ?
            ORDER BY ID ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT Category, SUM(Amount) AS total_amount
            FROM Expenses
            WHERE Date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND Category = ?"
            params.append(category)

        query += " GROUP BY Category ORDER BY Category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="http", host='0.0.0.0', port=3001)