
import os
import json
from collections import OrderedDict

from dotenv import load_dotenv
from google import genai
from google.genai import types

from services.sql_validator import validate_sql

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=API_KEY)

# Cache only successfully generated and validated SQL
query_cache = OrderedDict()
CACHE_LIMIT = 100


def clean_response(response_text):
    """Remove optional Markdown JSON fences."""
    text = response_text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "").strip()

    return text


def generate_sql(question, schema):

    if not question or not question.strip():
        raise ValueError("Please enter a question.")

    normalized_question = " ".join(question.lower().split())
    schema_key = json.dumps(schema, sort_keys=True)
    cache_key = (normalized_question, schema_key)

    # Return only previously validated SQL
    if cache_key in query_cache:
        query_cache.move_to_end(cache_key)
        print("Query cache hit")
        return query_cache[cache_key]

    print("Generating SQL with Gemini...")

    schema_text = json.dumps(schema, indent=2)

    prompt = f"""
You are an expert MySQL query generator.

Your task is to determine whether the user's request can be
answered using the exact database schema provided.

DATABASE SCHEMA:
{schema_text}

USER QUESTION:
{question}

IMPORTANT REQUEST VALIDATION RULES:

1. Check whether the user explicitly requests a table that
   does not exist in the provided schema.

2. Check whether the user explicitly requests a column that
   does not exist in the relevant table.

3. NEVER silently replace an unknown table with another table.

4. NEVER silently replace an unknown column with another column.

5. NEVER guess a table or column name.

6. If the user requests an unavailable table or column,
   set request_valid to false.

7. For an unavailable table, explain which table is missing
   and list the available tables.

8. For an unavailable column, explain which column is missing
   and identify the relevant table.

9. If the question is vague but can reasonably be answered
   using the schema, make a reasonable interpretation.

10. If the request is valid, generate exactly one complete,
    executable MySQL SELECT query.

SQL RULES:

- Use only tables and columns in the schema.
- Use correct JOIN conditions.
- Use SUM() for total amounts and revenue.
- Use COUNT() for counting records.
- Use AVG() for average calculations.
- Use GROUP BY for grouped calculations.
- Use ORDER BY when sorting is requested.
- Do not use SELECT *.
- Only generate SELECT statements.
- Add LIMIT 100 when appropriate.
- Never generate INSERT, UPDATE, DELETE, DROP or other
  data-changing statements.

OUTPUT FORMAT:

Return ONLY valid JSON with exactly these keys:

{{
    "request_valid": true,
    "error": null,
    "sql": "SELECT ... LIMIT 100"
}}

For an invalid table or column, return:

{{
    "request_valid": false,
    "error": "Clear explanation of the unavailable table or column.",
    "sql": null
}}

Do not return Markdown or text outside the JSON.
"""

    last_error = None

    # Try generation up to two times
    for attempt in range(2):

        current_prompt = prompt

        if last_error:
            current_prompt += f"""

The previous response had this problem:
{last_error}

Return a corrected response following the exact JSON format.
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=current_prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )

        if not response.text:
            last_error = "Gemini returned an empty response."
            continue

        print(f"Generation attempt: {attempt + 1}")

        try:
            result = json.loads(clean_response(response.text))

            if not isinstance(result, dict):
                raise ValueError("Gemini returned an invalid response format.")

            request_valid = result.get("request_valid")

            if request_valid is False:
                error_message = result.get("error")

                if not error_message:
                    raise ValueError(
                        "The requested table or column is not available "
                        "in the database schema."
                    )

                raise ValueError(error_message)

            if request_valid is not True:
                raise ValueError(
                    "Could not verify whether the request matches "
                    "the database schema. Please rephrase your question."
                )

            sql = result.get("sql")

            if not isinstance(sql, str) or not sql.strip():
                raise ValueError("Gemini did not generate a SQL query.")

            sql = sql.strip().rstrip(";")

            print("Generated SQL:")
            print(sql)

            # Independent syntax, safety and question validation
            safe_sql = validate_sql(sql, question)

            # Cache only successfully validated SQL
            query_cache[cache_key] = safe_sql
            query_cache.move_to_end(cache_key)

            if len(query_cache) > CACHE_LIMIT:
                query_cache.popitem(last=False)

            return safe_sql

        except (ValueError, json.JSONDecodeError) as error:
            last_error = str(error)
            print("Generation/validation failed:", last_error)

            # Do not retry a clearly identified unavailable table/column.
            # The model's explicit invalid-request response is handled above.
            if isinstance(error, ValueError) and (
                "not available" in last_error.lower()
                or "does not exist" in last_error.lower()
                or "unavailable" in last_error.lower()
            ):
                raise

    raise ValueError(
        f"Could not generate a valid SQL query: {last_error}"
    )
