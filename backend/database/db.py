
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "queryai_db"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


def get_database_schema():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE,
                COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """, (os.getenv("DB_NAME", "queryai_db"),))

        rows = cursor.fetchall()

        schema = {}

        for row in rows:
            table = row["TABLE_NAME"]

            if table not in schema:
                schema[table] = []

            schema[table].append({
                "column": row["COLUMN_NAME"],
                "type": row["DATA_TYPE"],
                "key": row["COLUMN_KEY"]
            })

        return schema

    finally:
        cursor.close()
        connection.close()
