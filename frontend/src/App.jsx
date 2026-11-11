
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:5000/api";

function App() {
  const [question, setQuestion] = useState("");
  const [sql, setSql] = useState("");
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [history, setHistory] = useState([]);
  const [schema, setSchema] = useState({});
  const [expandedTable, setExpandedTable] = useState("");
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [generated, setGenerated] = useState(false);
  const [hasResults, setHasResults] = useState(false);

  useEffect(() => {
    loadSchema();
  }, []);

  const loadSchema = async () => {
    setSchemaLoading(true);

    try {
      const response = await fetch(`${API_URL}/schema`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to load schema");
      }

      setSchema(data.schema || {});
    } catch (err) {
      setError(`Schema Explorer: ${err.message}`);
    } finally {
      setSchemaLoading(false);
    }
  };

  const generateSQL = async () => {
    if (!question.trim()) {
      setError("Please enter a question first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setColumns([]);
    setRows([]);
    setHasResults(false);
    setGenerated(false);

    try {
      const response = await fetch(`${API_URL}/generate-sql`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "SQL generation failed");
      }

      setSql(data.sql);
      setGenerated(true);
      setMessage("SQL generated successfully. Review or edit it before execution.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const executeSQL = async () => {
    if (!sql.trim()) {
      setError("Generate or enter a SQL query first.");
      return;
    }

    setExecuting(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/execute-sql`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sql }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "SQL execution failed");
      }

      setColumns(data.columns || []);
      setRows(data.rows || []);
      setHasResults(true);

      setMessage(
        data.row_count === 0
          ? "Query executed successfully. No records found."
          : `Query executed successfully. ${data.row_count} records found.`
      );

      setHistory((previous) => [
        {
          id: Date.now(),
          question,
          sql,
          rowCount: data.row_count,
          time: new Date().toLocaleTimeString(),
        },
        ...previous,
      ].slice(0, 20));

    } catch (err) {
      setError(err.message);
      setHasResults(false);
    } finally {
      setExecuting(false);
    }
  };

  const downloadCSV = () => {
    if (!hasResults || columns.length === 0) {
      return;
    }

    const escapeCSV = (value) => {
      if (value === null || value === undefined) {
        return "";
      }

      const text = typeof value === "object"
        ? JSON.stringify(value)
        : String(value);

      return `"${text.replace(/"/g, '""')}"`;
    };

    const csvContent = [
      columns.map(escapeCSV).join(","),
      ...rows.map((row) =>
        columns.map((column) => escapeCSV(row[column])).join(",")
      ),
    ].join("\r\n");

    const blob = new Blob(["\uFEFF" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "queryai_results.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const loadHistory = (item) => {
    setQuestion(item.question);
    setSql(item.sql);
    setColumns([]);
    setRows([]);
    setHasResults(false);
    setError("");
    setMessage("Previous query loaded. Execute it to view results.");
    setGenerated(true);
  };

  const resetWorkspace = () => {
    setQuestion("");
    setSql("");
    setColumns([]);
    setRows([]);
    setError("");
    setMessage("");
    setGenerated(false);
    setHasResults(false);
  };

  const examples = [
    "Show all customers",
    "List the top 5 most expensive products",
    "Show total sales by customer",
    "Find orders with pending status",
  ];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">Q</div>
          <div>
            <h1>QueryAI</h1>
            <span>Natural Language to SQL</span>
          </div>
        </div>

        <div className="connection">
          <span className="status-dot"></span>
          MySQL Database
        </div>
      </header>

      <main className="main-container">
        <section className="welcome">
          <p className="eyebrow">AI-POWERED DATABASE ASSISTANT</p>
          <h2>Ask your data anything.</h2>
          <p>
            Convert plain English questions into SQL queries
            and explore your database instantly.
          </p>
        </section>

        <section className="workspace">
          <div className="section-heading">
            <h3>Ask a question</h3>
            <button className="text-button" onClick={resetWorkspace}>
              Clear workspace
            </button>
          </div>

          <textarea
            className="question-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: Show the top 5 customers by total order value..."
            rows={3}
          />

          <div className="examples">
            <span>Try asking:</span>
            {examples.map((example) => (
              <button
                key={example}
                onClick={() => setQuestion(example)}
              >
                {example}
              </button>
            ))}
          </div>

          <button
            className="primary-button"
            onClick={generateSQL}
            disabled={loading}
          >
            {loading ? "Generating SQL..." : "✦ Generate SQL"}
          </button>
        </section>

        {error && (
          <div className="alert error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {message && (
          <div className="alert success">
            {message}
          </div>
        )}

        {generated && (
          <section className="result-section">
            <div className="section-heading">
              <div>
                <h3>Generated SQL</h3>
                <p>Review or edit the query before running it.</p>
              </div>
              <span className="readonly-badge">SELECT ONLY</span>
            </div>

            <textarea
              className="sql-editor"
              value={sql}
              onChange={(e) => setSql(e.target.value)}
              rows={8}
              spellCheck={false}
            />

            <button
              className="execute-button"
              onClick={executeSQL}
              disabled={executing}
            >
              {executing ? "Executing..." : "▶ Execute Query"}
            </button>
          </section>
        )}

        {hasResults && (
          <section className="result-section">
            <div className="section-heading">
              <div>
                <h3>Query Results</h3>
                <p>{rows.length} records returned</p>
              </div>

              <div className="result-actions">
                <span className="result-count">
                  {rows.length} Rows
                </span>

                {columns.length > 0 && (
                  <button
                    className="execute-button"
                    onClick={downloadCSV}
                  >
                    ↓ Download CSV
                  </button>
                )}
              </div>
            </div>

            {columns.length === 0 ? (
              <p>No columns or records returned.</p>
            ) : rows.length === 0 ? (
              <p>No records found for this query.</p>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      {columns.map((column) => (
                        <th key={column}>{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, index) => (
                      <tr key={index}>
                        {columns.map((column) => (
                          <td key={column}>
                            {row[column] === null
                              ? "NULL"
                              : typeof row[column] === "object"
                                ? JSON.stringify(row[column])
                                : String(row[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        <section className="history-section">
          <div className="section-heading">
            <div>
              <h3>Schema Explorer</h3>
              <p>Explore available database tables and columns.</p>
            </div>

            <button
              className="text-button"
              onClick={loadSchema}
              disabled={schemaLoading}
            >
              {schemaLoading ? "Loading..." : "↻ Refresh"}
            </button>
          </div>

          {Object.keys(schema).length === 0 ? (
            <p>{schemaLoading ? "Loading database schema..." : "No tables found."}</p>
          ) : (
            <div className="schema-list">
              {Object.entries(schema).map(([tableName, tableColumns]) => (
                <div className="schema-table" key={tableName}>
                  <button
                    className="history-item"
                    onClick={() =>
                      setExpandedTable(
                        expandedTable === tableName ? "" : tableName
                      )
                    }
                  >
                    <div>
                      <strong>▣ {tableName}</strong>
                      <span>{tableColumns.length} columns</span>
                    </div>
                    <span>
                      {expandedTable === tableName ? "−" : "+"}
                    </span>
                  </button>

                  {expandedTable === tableName && (
                    <div className="schema-columns">
                      {tableColumns.map((column) => (
                        <div
                          className="schema-column"
                          key={column.column}
                        >
                          <span>{column.column}</span>
                          <span>{column.type}</span>
                          {column.key && (
                            <span className="readonly-badge">
                              {column.key === "PRI" ? "PRIMARY KEY" : column.key}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {history.length > 0 && (
          <section className="history-section">
            <div className="section-heading">
              <div>
                <h3>Query History</h3>
                <p>Your recent executed queries in this session.</p>
              </div>

              <button
                className="text-button"
                onClick={() => setHistory([])}
              >
                Clear history
              </button>
            </div>

            {history.map((item) => (
              <button
                className="history-item"
                key={item.id}
                onClick={() => loadHistory(item)}
              >
                <div>
                  <strong>{item.question || "Manual SQL query"}</strong>
                  <span>{item.time} · {item.rowCount} rows</span>
                </div>
                <span>View →</span>
              </button>
            ))}
          </section>
        )}

        <footer>
          QueryAI · Built with React, Flask, MySQL and Gemini AI
        </footer>
      </main>
    </div>
  );
}

export default App;
