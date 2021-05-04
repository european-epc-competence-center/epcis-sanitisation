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

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import RedirectResponse

from pydantic import BaseModel

import uvicorn
import argparse
import sys
import logging
import json

from tinydb import TinyDB, Query


app = FastAPI()
db = TinyDB('db.json')


class XmlWrapper(BaseModel):
    xml_epcis_document: str


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse("/docs")


@app.get("/event/{ni}")
def get_sanitised_event(ni: str):
    raise HTTPException(status_code=404, detail="Event not found")
    # return {"item_id": item_id}


@app.post("/sanitise_json_event/")
def sanitise_and_store_json_event(json_event: dict = Body(...)):
    """
    Post an epcis event in JSON format to store a sanitised version.
    """
    events = json_to_py.event_list_from_epcis_document_json(json_event)

    return __sanitise_events(events)


@app.post("/sanitise_xml_event/")
def sanitise_and_store_xml_event(xml_doc: XmlWrapper):
    """
    Post an epcis event in XML format to store a sanitised version.
    """

    events = xml_to_py.event_list_from_epcis_document_str(
        xml_doc.xml_epcis_document)
    return __sanitise_events(events)


def __sanitise_events(events):

    UniqueDoc = Query()
    stored_config = db.search(UniqueDoc.id == "config")[0]
    args = stored_config["args"]
    config = stored_config["config"]

    logging.debug("\n\nEvents received:\n{}".format(events))
    logging.debug("args:{}".format(args))
    logging.debug("config:{}".format(config))

    sanitised_events = sanitiser.sanitise_events(
        events=events, hashalg=args["algorithm"], dead_drop_url=args["dead_drop_url"], config=config)

    return {"sanitised_events": sanitised_events}


def __command_line_parsing(argv):
    logger_cfg = {
        "format":
            "%(asctime)s %(funcName)s (%(lineno)d) [%(levelname)s]:    %(message)s"
    }

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

    args = parser.parse_args(argv)

    logger_cfg["level"] = getattr(logging, args.log)
    logging.basicConfig(**logger_cfg)

    # print("Log messages above level: {}".format(logger_cfg["level"]))

    return args


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

    uvicorn.run("webservice:app",
                host=args["host"],
                port=int(args["port"]),
                log_level=args["log"].lower(),
                reload=args["reload"]
                )


# start uvicorn if run as main
if __name__ == "__main__":
    main(sys.argv[1:])
