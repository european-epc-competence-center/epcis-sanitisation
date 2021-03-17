try:
    from .context import epcis_sanitiser
except ImportError:
    from context import epcis_sanitiser  # noqa: F401

from epcis_sanitiser.__main__ import main

import logging


def test_main(caplog):
    caplog.set_level(logging.DEBUG)
    main(["events/ReferenceEventHashAlgorithm.xml"])
