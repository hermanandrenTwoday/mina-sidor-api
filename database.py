import os
import mssql_python


CONNECTION_STRING_SETTINGS = {
    "dev": "SQL_CONNECTION_STRING_DEV",
    "prod": "SQL_CONNECTION_STRING_PROD",
}


def execute_select(
    query: str, parameters: dict, database: str = "prod"
) -> list[dict]:
    setting_name = CONNECTION_STRING_SETTINGS.get(database)

    if not setting_name:
        raise ValueError(f"Unknown database target: {database}")

    connection_string = os.environ.get(setting_name)

    if not connection_string:
        raise RuntimeError(f"{setting_name} is not configured.")

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
