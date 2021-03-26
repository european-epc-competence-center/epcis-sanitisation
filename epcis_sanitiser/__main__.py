#!/usr/bin/python3
"""

.. module:: main
   :synopsis: Command line utility to calculate sanitised EPCIS events
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


import argparse
import logging
import sys
from epcis_event_hash_generator import events_from_file_reader


def __command_line_parsing(args):
    logger_cfg = {
        "format":
            "%(asctime)s %(funcName)s (%(lineno)d) [%(levelname)s]:    %(message)s"
    }

    parser = argparse.ArgumentParser(
        description="Generate a sanitised EPCIS event from an EPCIS Document.")
    parser.add_argument("file", help="EPCIS file", nargs="+")
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
        default="WARNING")
    parser.add_argument(
        "-b",
        "--batch",
        help="If given, write the output for each input file into a sibling output file "
             "with the same name + '.sanitised.json' instead of stdout.",
        action="store_true")
    parser.add_argument(
        "-d",
        "--dead-drop-url",
        help="URL to dead drop for requesting the full event data",
        default="")

    args = parser.parse_args(args)

    logger_cfg["level"] = getattr(logging, args.log)
    logging.basicConfig(**logger_cfg)

    # print("Log messages above level: {}".format(logger_cfg["level"]))

    if not args.file:
        logging.critical("File name required.")
        parser.print_help()
        sys.exit(1)
    else:
        logging.debug("reading from files: '{}'".format(args.file))

    return args


def main(argv):
    """The main function reads the path to the epcis file
    and optionaly the hash algorithm from the command
    line arguments and calls the actual algorithm.
    """

    args = __command_line_parsing(argv)

    # Never log anything before calling logging.basicConfig !
    logging.debug("Running cli tool with arguments %s", argv)

    for filename in args.file:
        events = events_from_file_reader.event_list_from_file(filename)

        logging.debug(
            "\n\nEvents contained in '{}':\n{}".format(filename, events))

        sanitised_events = sanitiser.sanitise_events(
            events=events, hashalg=args.algorithm, dead_drop_url=args.dead_drop_url)

        print("\nSanitised Events:")
        for event in sanitised_events:
            print("\n")
            print(event)


# goto main if script is run as entrypoint
if __name__ == "__main__":
    main(sys.argv[1:])
