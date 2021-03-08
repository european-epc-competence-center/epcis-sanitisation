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

import argparse
import logging
from epcis_event_hash_generator import events_from_file_reader, hash_generator


def __command_line_parsing():
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

    args = parser.parse_args()

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


def main():
    """The main function reads the path to the epcis file
    and optionaly the hash algorithm from the command
    line arguments and calls the actual algorithm.
    """

    args = __command_line_parsing()

    logging.debug("Running cli tool with arguments %s", args)

    for filename in args.file:
        events = events_from_file_reader.event_list_from_file(filename)

        prehashes = hash_generator.derive_prehashes_from_events(events)
        hashes = hash_generator.calculate_hashes_from_pre_hashes(prehashes)

        print("\n\nEvents contained in '{}':\n{}".format(filename, events))
        print("\n\nHashes of the events contained in '{}':\n".format(filename) + "\n".join(hashes))
        print("\nPre-hash strings:\n" + "\n---\n".join(prehashes))


# goto main if script is run as entrypoint
if __name__ == "__main__":
    main()
