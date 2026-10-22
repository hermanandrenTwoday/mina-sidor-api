import azure.functions as func
import json
import logging
import socket
import time
from database import execute_select



app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "healthy"}),
        status_code=200,
        mimetype="application/json",
    )

@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    host = req.params.get("host", "10.247.2.77")
    port = int(req.params.get("port", "1433"))

    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=5) as s:
            ms = round((time.perf_counter() - start) * 1000, 1)
            return func.HttpResponse(
                f"OK: reached {host}:{port} in {ms} ms "
                f"(source IP {s.getsockname()[0]})"
            )
    except Exception as e:
        ms = round((time.perf_counter() - start) * 1000, 1)
        return func.HttpResponse(
            f"FAILED: {host}:{port} after {ms} ms - {type(e).__name__}: {e}",
            status_code=502,
        )


@app.route(route="KundKontaktPerson", methods=["GET"])
def KundKontaktPerson(req: func.HttpRequest) -> func.HttpResponse:
    personnr = req.params.get("personnr")

    if not personnr:
        return func.HttpResponse(
            "Missing 'personnr' query parameter.",
            status_code=400,
        )

    if not personnr.isdigit():
        return func.HttpResponse(
            "Invalid 'personnr' format. It should be a number.",
            status_code=400,
        )

    query = """
        SELECT intKundNr, strForNamn, strEfterNamn
        FROM [TX_MDW_Dev].[MDW].[tbFuKundKontaktperson]
        WHERE strPersonnr = %(personnr)s;
    """

    try:
        rows = execute_select(query, {"personnr": personnr})
    except Exception as error:
        logging.exception("Database request failed.")
        return func.HttpResponse(
            (
                f"Database request failed: {type(error).__name__}: {error}"
            ),
            status_code=500,
        )

    return func.HttpResponse(
        json.dumps({"data": rows}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="AnlaggningsKontaktperson", methods=["GET"])
def AnlaggningsKontaktperson(req: func.HttpRequest) -> func.HttpResponse:
    kundnr = req.params.get("kundnr")

    if not kundnr:
        return func.HttpResponse(
            "Missing 'kundnr' query parameter.",
            status_code=400,
        )

    if not kundnr.isdigit():
            return func.HttpResponse(
                "Invalid 'kundnr' format. It should be a number.",
                status_code=400,
            )

    query = """
        SELECT intRecnum, intKundNr, strAnlnr, strPersonnr, strForNamn, strEfterNamn, strEpostadress, strTelefonMobil, strTelefon
        FROM [TX_MDW_Dev].[MDW].[tbFuAnlaggningsKontaktperson]
        WHERE intKundNr = %(kundnr)s;
    """
    try:
        rows = execute_select(query, {"kundnr": kundnr})
    except Exception as error:
        logging.exception("Database request failed.")
        return func.HttpResponse(
            f"Database request failed: {type(error).__name__}: {error}",
            status_code=500,
        )

    return func.HttpResponse(
        json.dumps({"data": rows}),
        status_code=200,
        mimetype="application/json",
    )
