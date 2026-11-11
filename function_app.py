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
        FROM [TX_MDW_Prod].[MDW].[tbFuKundKontaktperson]
        WHERE strPersonnr = %(personnr)s;
    """

    try:
        rows = execute_select(query, {"personnr": personnr}, database="prod")
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
        FROM [TX_MDW_Prod].[MDW].[tbFuAnlaggningsKontaktperson]
        WHERE intKundNr = %(kundnr)s;
    """
    try:
        rows = execute_select(query, {"kundnr": kundnr}, database="prod")
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

@app.route(route="KopHistorik", methods=["GET"])
def KopHistorik(req: func.HttpRequest) -> func.HttpResponse:
    kundnr = req.params.get("kundnr")
    fromDate = req.params.get("fromDate")
    toDate = req.params.get("toDate")

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
    if not fromDate or not toDate:
        return func.HttpResponse(
            "Missing 'fromDate' or 'toDate' query parameter.",
            status_code=400,
        )

    query = """
        SELECT
            [Anläggningsnummer] AS anlaggningsnummer,
            [Anläggningsadress] AS anlaggningsadress,
            [Produkt] AS produkt,
            [Tjänst] AS tjanst,
            [Avser] AS avser,
            [Enhet] AS enhet,
            SUM([SumBelopp]) AS nettoforsaljning,
            SUM([SumAntal]) AS antal
        FROM [TX_MDW_Prod].[MDW].[Köphistorik]
        WHERE [Kundnummer] = %(kundnr)s
        AND [FakturadatumÅrMånad] BETWEEN %(fromDate)s AND %(toDate)s
        GROUP BY
            [Anläggningsnummer],
            [Anläggningsadress],
            [Produkt],
            [Tjänst],
            [Avser],
            [Enhet]
        ORDER BY
            [Anläggningsnummer],
            [Produkt],
            [Tjänst],
            [Avser];
"""

    try:
        rows = execute_select(query, {"kundnr": kundnr, "fromDate": fromDate, "toDate": toDate}, database="prod")
    except Exception as error:
        logging.exception("Database request failed.")
        return func.HttpResponse(
            f"Database request failed: {type(error).__name__}: {error}",
            status_code=500,
        )

    data = [
        {
            "anlaggning": {
                "nummer": str(row["anlaggningsnummer"]),
                "adress": row["anlaggningsadress"],
            },
            "produkt": row["produkt"],
            "tjanst": row["tjanst"],
            "avser": row["avser"],
            "enhet": row["enhet"],
            "nettoforsaljning": row["nettoforsaljning"],
            "antal": row["antal"],
        }
        for row in rows
    ]

    payload = {
        "rapportperiod": {
            "fran": fromDate,
            "tom": toDate,
        },
        "kundnummer": int(kundnr),
        "data": data,
    }

    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False, default=float),
        status_code=200,
        mimetype="application/json",
    )

@app.route(route="MiljorapportFjarrvarme", methods=["GET"])
def MiljorapportFjarrvarme(req: func.HttpRequest) -> func.HttpResponse:
    Anlaggningsnummer = req.params.get("Anlaggningsnummer")
    periodFran = req.params.get("periodFran")
    periodTom = req.params.get("periodTom")

    if not Anlaggningsnummer:
        return func.HttpResponse(
            "Missing 'Anlaggningsnummer' query parameter.",
            status_code=400,
        )               

    if not periodFran or not periodTom:
        return func.HttpResponse(
            "Missing 'periodFran' or 'periodTom' query parameter.",
            status_code=400,
        )

    query = """
        SELECT
            [Anläggningsnummer],
            [Adress],
            SUM([ForbrukningKwh]) AS [ForbrukningKwh],
            SUM([Co2Utsläpp]) AS [Co2Utsläpp],
            [Taxa] AS [Taxa]
        FROM [TX_MDW_Prod].[MDW].[MiljörapportFjärrvärme]
        WHERE [Anläggningsnummer] = %(Anlaggningsnummer)s
        AND [PeriodÅrMånad] BETWEEN %(periodFran)s AND %(periodTom)s
        GROUP BY
            [Anläggningsnummer],
            [Adress],
            [Taxa]
        order by Taxa;
    """

    try:
        rows = execute_select(query, {"Anlaggningsnummer": Anlaggningsnummer,
                                       "periodFran": periodFran,
                                        "periodTom": periodTom},
                             database="prod")
    except Exception as error:
        logging.exception("Database request failed.")
        return func.HttpResponse(
            f"Database request failed: {type(error).__name__}: {error}",
            status_code=500,
        )   

    data = [
        {
            "rapportFran": periodFran,
            "rapportTom": periodTom,
            "anlaggningsnummer": str(row["Anläggningsnummer"]),
            "adress": row["Adress"],
            "forbrukningKwh": row["ForbrukningKwh"],
            "co2UtslappGram": row["Co2Utsläpp"],
            "taxa": row["Taxa"],
        }
        for row in rows
    ]

    payload = {
        "data": data,
    }

    return func.HttpResponse(
        json.dumps(payload, ensure_ascii=False, default=float),
        status_code=200,
        mimetype="application/json",
    )
