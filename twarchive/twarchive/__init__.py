#!/usr/bin/env python3

import logging

from twarchive import version


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


__version__ = version.__version__
