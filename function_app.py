import azure.functions as func
import json
import logging
import os

import mssql_python

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="db-test", methods=["GET"])
def db_test(req: func.HttpRequest) -> func.HttpResponse:
    #dev connection string: "Server=CX34SB4;Database
    connection_string = os.environ.get("SQL_CONNECTION_STRING")

    personnr = req.params.get("personnr")

    if not personnr:
        return func.HttpResponse(
            "Missing 'personnr' query parameter.",
            status_code=400,
        )

    if not personnr.isdigit() or len(personnr) != 12:
        return func.HttpResponse(
            "Invalid 'personnr' format. It should be a 12-digit number.",
            status_code=400,
        )

    #dev connection string: "Server=CX34SB4;Database
    if not connection_string:
        return func.HttpResponse(
            "SQL_CONNECTION_STRING is not configured.",
            status_code=500,
        )

    query = """
        SELECT intKundNr
        FROM dbo.tbFuKundKontaktperson
        WHERE strPersonnr = %(personnr)s;
    """

    try:
        connection = mssql_python.connect(connection_string, timeout=5)
        try:
            cursor = connection.cursor()
            cursor.execute(query, {"personnr": personnr})
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            connection.close()
    except mssql_python.Error:
        logging.exception("Database request failed.")
        return func.HttpResponse(
            "Database request failed.",
            status_code=500,
        )

    return func.HttpResponse(
        json.dumps({"data": rows}),
        status_code=200,
        mimetype="application/json",
    )


