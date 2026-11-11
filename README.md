# QueryAI – Natural Language to SQL

QueryAI is an AI-powered database assistant that converts natural language questions into SQL queries using Google's Gemini API. Users can review and edit generated SQL, execute queries, and explore database results through a simple web interface.

## Features

- **Natural Language to SQL:** Generate MySQL queries from plain English questions using Gemini AI.
- **Editable SQL:** Review and modify generated SQL before execution.
- **SQL Validation:** Validate queries and restrict execution to safe, read-only SELECT statements and approved tables.
- **Query Execution:** Execute SQL queries and display results in a structured table.
- **CSV Export:** Download query results as CSV files.
- **Schema Explorer:** Explore database tables, column names, data types, and keys.
- **Query History:** View and reload recently executed queries.
- **Query Caching:** Cache validated SQL generation results to reduce repeated Gemini API calls.
- **Error Handling:** Handle invalid questions, SQL errors, and empty results with understandable messages.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite, CSS |
| Backend | Python, Flask |
| Database | MySQL |
| AI Integration | Google Gemini API |
| SQL Validation | SQLGlot |
| API Communication | REST API, Fetch |

## Project Structure

```text
QueryAI/
│
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   └── schema.sql
│   └── services/
│       ├── __init__.py
│       ├── sql_generator.py
│       └── sql_validator.py
│
├── frontend/
│   ├── public/
│   │   └── queryai.svg
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   └── package.json
│
├── .gitignore
└── README.md
```

## Database Setup

1. Install MySQL Server and MySQL Workbench.
2. Create a database named `queryai_db`.
3. Execute the SQL statements in `backend/database/schema.sql` to create the required tables and data, if included.
4. Configure your database credentials in `backend/.env`.

## Backend Setup

Open a terminal:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` and provide your own credentials:

```env
DB_HOST=localhost
DB_USER=root
DB