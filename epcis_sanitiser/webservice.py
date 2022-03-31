#!/usr/bin/python3
"""

.. module:: webservice
   :synopsis: Webservice to calculate sanitised EPCIS events
              https://github.com/european-epc-competence-center/epcis-sanitisation

.. moduleauthor:: Sebastian Schmittner <sebastian.schmittner@eecc.de>

Copyright 2021 Sebastian Schmittner

This program is free software: you can redistribute it and/or modify
it under the terms given in the LICENSE file.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the LICENSE
file for details.

"""

try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

from epcis_sanitiser import sanitiser


from epcis_event_hash_generator import json_to_py
from epcis_event_hash_generator import xml_to_py

from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import RedirectResponse
from fastapi.openapi.utils import get_openapi

import uvicorn
import argparse
import sys
import logging
import json

from tinydb import TinyDB, Query


app = FastAPI()
db = TinyDB('db.json')


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse("docs")


@app.get("/db_dump")
def get_all_sanitised_event():
    """
    Get a complete DB dump including ALL events.
    This should only be used for debugging purposes, since no pagination is implemented.
    """
    return db.all()


@app.get("/event/{eventHash}")
def get_sanitised_event(eventHash: str):
    """
    Takes the eventID without the ni:/// prefix and returns the matching
    sanitised event, if any.
    """
    eventId = r"ni:///" + eventHash
    logging.debug("looking for event %s", eventId)

    Event = Query()
    events = db.search(Event.eventId == eventId)
    if events:
        return events

    raise HTTPException(
        status_code=404, detail="No event with id {} found".format(eventId))


@app.get("/events_for_epc/{epcHash}")
def get_sanitised_event_by_epc(epcHash: str):
    """
    Takes the epc NI without the ni:/// prefix and returns all matching
    sanitised events, if any.
    This lookup scans in epc, input, output, child and parent list,
    as well as in the child, input and output quantity lists.
    """
    __set_logging_cfg_from_db()
    epc = r"ni:///" + epcHash
    logging.debug("looking for event with epc %s", epc)

    Event = Query()
    events = db.search(Event.epcList.test(lambda val: epc in val))
    events += db.search(Event.inputEPCList.test(lambda val: epc in val))
    events += db.search(Event.outputEPCList.test(lambda val: epc in val))
    events += db.search(Event.childEPCs.test(lambda val: epc in val))
    events += db.search(Event.parentID == epc)

    events += db.search(Event.quantityList.test(lambda val: epc in val))
    events += db.search(Event.childQuantityList.test(lambda val: epc in val))
    events += db.search(Event.inputQuantityList.test(lambda val: epc in val))
    events += db.search(Event.outputQuantityList.test(lambda val: epc in val))

    if events:
        return events

    raise HTTPException(
        status_code=404, detail="No event with id {} found".format(epcHash))


@app.post("/sanitise_json_event/")
def sanitise_and_store_json_event(json_events: dict = Body(...)):
    """
    Post an epcis event in JSON format to store a sanitised version.
    """
    __set_logging_cfg_from_db()
    logging.debug("Sanitising JSON events %s", json_events)
    events = json_to_py.event_list_from_epcis_document_json(json_events)

    return __sanitise_and_store_events(events)


@app.post("/sanitise_xml_event/")
async def sanitise_and_store_xml_event(request: Request):
    """
    Post an epcis event in XML format to store a sanitised + hashed version in the discovery service.
    Also returns the stored data.
    """
    __set_logging_cfg_from_db()

    body = await request.body()
    if not body:
        raise HTTPException(
            status_code=400, detail="Expecting XML Body")

    xml_doc = body.decode('utf-8')
    logging.debug("Sanitising XML events:\n %s", xml_doc)

    events = xml_to_py.event_list_from_epcis_document_str(xml_doc)
    return __sanitise_and_store_events(events)


def __set_logging_cfg_from_db():
    UniqueDoc = Query()
    stored_config = db.search(UniqueDoc.id == "config")[0]
    args = stored_config["args"]
    logging.basicConfig(**__logger_cfg(args["log"]))
    logging.debug("Setting log level: %s", args["log"])


def __sanitise_and_store_events(events):

    UniqueDoc = Query()
    stored_config = db.search(UniqueDoc.id == "config")[0]
    args = stored_config["args"]
    config = stored_config["config"]

    logging.debug("\n\nEvents received:\n{}".format(events))
    logging.debug("args:{}".format(args))
    logging.debug("config:{}".format(config))

    sanitised_events = sanitiser.sanitise_events(
        events=events, hashalg=args["algorithm"], dead_drop_url=args["dead_drop_url"], config=config)

    for event in sanitised_events:
        db.insert(event)

    return {"sanitised_events": sanitised_events}


def __logger_cfg(log_lvl):
    level = getattr(logging, log_lvl)
    re = {
        "format": "%(asctime)s %(funcName)s (%(lineno)d) [%(levelname)s]: %(message)s"}
    re["level"] = level
    return re


def __command_line_parsing(argv):

    parser = argparse.ArgumentParser(
        description="Run Webservice that generates and stores sanitised EPCIS events.")
    parser.add_argument(
        "-a",
        "--algorithm",
        help="Hashing algorithm to use.",
        choices=["sha256", "sha3_256", "sha384", "sha512"],
        default="sha256")
    parser.add_argument(
        "-l",
        "--log",
        help="Set the log level. Default: INFO.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO")
    parser.add_argument(
        "-d",
        "--dead-drop-url",
        help="URL to dead drop for requesting the full event data",
        default="")
    parser.add_argument(
        "-c",
        "--sanitisation-config-file",
        help="JSON file containing a dictionary of fields to be included in the sanitised" +
        " events -> hash salt to be used." +
        " Set the salt to empty string for unsalted hashing " +
        "and to None for including the clear text value without hashing"
    )
    parser.add_argument(
        "-H",
        "--host",
        help="Hostname to run the webservice.",
        default="127.0.0.1"
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Port to run the webservice.",
        default="8080"
    )
    parser.add_argument(
        "-r",
        "--reload",
        help="Development option: automatically reload if python sources change",
        action="store_true",
        default=False)
    parser.add_argument(
        "-R",
        "--root-path",
        help=" Set the ASGI root_path for applications submounted below a given URL path."
    )

    args = parser.parse_args(argv)

    logging.basicConfig(**__logger_cfg(args.log))
    logging.debug("Setting log level: %s(%s)", args.log,
                  __logger_cfg(args.log)["level"])

    return args


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="EPCIS Sanitisation Demonstration API",
        version="1.0.0",
        description="This is a Webservice to calculate " +
        "<a href='https://github.com/european-epc-competence-center/epcis-sanitisation'>sanitised EPCIS events</a>.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://eecc.info/img/eecc/logo_213x182.png"
    }
    openapi_schema["paths"]["/sanitise_xml_event/"]["post"]["requestBody"] = {
        "content": {
            "application/xml": {"schema": {"title": "XML EPCIS Document", "type": "string"}}
        },
        "required": True
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def main(argv):

    config = epcis_sanitiser.DEFAULT_CONFIG
    args = vars(__command_line_parsing(argv))

    if args["sanitisation_config_file"]:
        with open(args["sanitisation_config_file"], 'r') as file:
            data = file.read()
        new_config = json.loads(data)
        for key, val in new_config.items():  # only overwrite given keys
            config[key] = val

    UniqueDoc = Query()
    db.remove(UniqueDoc.id == "config")
    db.insert({"id": "config", "args": args, "config": config})

    uvicorn_args = {"host": args["host"],
                    "port": int(args["port"]),
                    "log_level": args["log"].lower(),
                    "reload": args["reload"]
                    }

    if args["root_path"]:
        uvicorn_args["root_path"] = args["root_path"]

    uvicorn.run("webservice:app", **uvicorn_args)


# start uvicorn if run as main
if __name__ == "__main__":
    main(sys.argv[1:])
