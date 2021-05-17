#!/usr/bin/python3
"""

.. module:: dead_drop
   :synopsis: Webservice to facilitate requests for resources to an unknown / anonymous
              party.

.. moduleauthor:: Sebastian Schmittner <sebastian.schmittner@eecc.de>

Copyright 2021 Sebastian Schmittner

This program is free software: you can redistribute it and/or modify
it under the terms given in the LICENSE file.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the LICENSE
file for details.

"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
from typing import Optional, List

import uvicorn
import argparse
import sys
import logging

from tinydb import TinyDB, Query

from datetime import datetime, timedelta

DEFAULT_LIFETIME_IN_DAYS = 30
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

app = FastAPI()
db = TinyDB('dead_drop_db.json')


class Adress(BaseModel):
    endpoint: str
    protocol: Optional[str]

    def asdict(self):
        re = {"endpoint": self.endpoint}
        if self.protocol:
            re["protocol"] = self.protocol
        return re


class Authorisation(BaseModel):
    id: str
    credentials: Optional[dict]

    def asdict(self):
        re = {"id": self.id}
        if self.credentials:
            re["credentials"] = self.credentials
        return re


class Request(BaseModel):
    requesting: str
    recipient: Adress
    auth: Optional[Authorisation]
    valid_until: Optional[datetime]

    def asdict(self):
        re = {"requesting": self.requesting,
              "recipient": self.recipient.asdict()
              }
        if self.auth:
            re["auth"] = self.auth.asdict()
        if self.valid_until:
            re["valid_until"] = self.valid_until.strftime(DATE_FORMAT)

        return re


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse("docs")


@app.put("/request/")
def store_request(request: Request) -> str:
    if not request.valid_until:
        request.valid_until = datetime.now() + timedelta(days=DEFAULT_LIFETIME_IN_DAYS)
    db.insert(request.asdict())
    return "Request stored"


@app.get("/request/{requesting}")
def find_request(requesting: str) -> List[Request]:
    __remove_old_requests()
    logging.debug("looking for '%s'", requesting)
    matches = db.search(Query().requesting == requesting)
    logging.debug("found %s", matches)
    logging.debug("all: %s", db.all())
    if matches:
        return matches

    raise HTTPException(
        status_code=404, detail="No requests requesting '{}' found".format(requesting))


def __remove_old_requests():
    removed = db.remove(Query().valid_until.test(
        lambda valid: datetime.strptime(valid, DATE_FORMAT) > datetime.now()))
    logging.debug("removed old requests: %s", removed)


def __command_line_parsing(argv):
    logger_cfg = {
        "format":
            "%(asctime)s %(funcName)s (%(lineno)d) [%(levelname)s]:    %(message)s"
    }

    parser = argparse.ArgumentParser(
        description="Run Webservice that facilitates requests to anonymous "
        + "ressource owners by providing a public notes board.")
    parser.add_argument(
        "-l",
        "--log",
        help="Set the log level. Default: INFO.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO")
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

    logger_cfg["level"] = getattr(logging, args.log)
    logging.basicConfig(**logger_cfg)
    logging.debug("Setting log level: %s(%s)", args.log, logger_cfg["level"])

    # print("Log messages above level: {}".format(logger_cfg["level"]))

    return args


def main(argv):

    args = vars(__command_line_parsing(argv))

    uvicorn_args = {"host": args["host"],
                    "port": int(args["port"]),
                    "log_level": args["log"].lower(),
                    "reload": args["reload"]
                    }

    if args["root_path"]:
        uvicorn_args["root_path"] = args["root_path"]

    uvicorn.run("dead_drop:app", **uvicorn_args)


# start uvicorn if run as main
if __name__ == "__main__":
    main(sys.argv[1:])
