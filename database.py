import os
import mssql_python


def execute_select(query: str, parameters: dict) -> list[dict]:
    connection_string = os.environ.get("SQL_CONNECTION_STRING_DEV")

    if not connection_string:
        raise RuntimeError("SQL_CONNECTION_STRING_DEV is not configured.")

    connection = None

    try:
        connection = mssql_python.connect(connection_string, timeout=5)

        cursor = connection.cursor()
        cursor.execute(query, parameters)

        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        if connection is not None:
            connection.close()