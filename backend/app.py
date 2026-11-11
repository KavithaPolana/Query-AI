
from flask import Flask, request, jsonify
from flask_cors import CORS
from database.db import get_connection, get_database_schema
from services.sql_generator import generate_sql
from services.sql_validator import validate_sql
import csv
import io
from flask import Response

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"]
    }
})


@app.route("/api/health", methods=["GET"])
def health():
    try:
        connection = get_connection()
        connection.close()

        return jsonify({
            "status": "success",
            "message": "QueryAI backend and database connected"
        })

    except Exception:
        app.logger.exception("Health check failed")
        return jsonify({
            "status": "error",
            "message": "Backend or database connection failed"
        }), 500


@app.route("/api/schema", methods=["GET"])
def get_schema():
    try:
        schema = get_database_schema()

        return jsonify({
            "success": True,
            "schema": schema
        })

    except Exception:
        app.logger.exception("Schema retrieval failed")
        return jsonify({
            "success": False,
            "error": "Unable to retrieve database schema"
        }), 500


@app.route("/api/generate-sql", methods=["POST"])
def generate_query():
    try:
        data = request.get_json(silent=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "error": "Please enter a question"
            }), 400

        if len(question) > 500:
            return jsonify({
                "error": "Question must be 500 characters or less"
            }), 400

        schema = get_database_schema()
        sql = generate_sql(question, schema)
        safe_sql = validate_sql(sql)

        return jsonify({
            "success": True,
            "question": question,
            "sql": safe_sql
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("SQL generation failed")
        return jsonify({
            "success": False,
            "error": "SQL generation failed. Please try again."
        }), 500


@app.route("/api/execute-sql", methods=["POST"])
def execute_query():
    connection = None
    cursor = None

    try:
        data = request.get_json(silent=True) or {}
        sql = data.get("sql", "").strip()

        if not sql:
            return jsonify({
                "error": "SQL query is required"
            }), 400

        # Validate edited SQL again before execution.
        safe_sql = validate_sql(sql)

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(safe_sql)

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        return jsonify({
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("SQL execution failed")
        return jsonify({
            "success": False,
            "error": "SQL execution failed. Please check your query."
        }), 400

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
