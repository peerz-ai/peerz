import os
import re
from typing import Union

import requests
from hivemind.utils.logging import TextStyle, get_logger
from packaging.version import parse

import peerz

logger = get_logger(__name__)


def validate_version() -> None:
    logger.info(f"Running {TextStyle.BOLD}Peerz {peerz.__version__}{TextStyle.RESET}")
    try:
        r = requests.get("https://pypi.python.org/pypi/peerz/json")
        r.raise_for_status()
        response = r.json()

        versions = [parse(ver) for ver in response.get("releases")]
        latest = max(ver for ver in versions if not ver.is_prerelease)

        if parse(peerz.__version__) < latest:
            logger.info(
                f"A newer version {latest} is available. Please upgrade with: "
                f"{TextStyle.BOLD}pip install --upgrade peerz{TextStyle.RESET}"
            )
    except Exception as e:
        logger.warning("Failed to fetch the latest Peerz version from PyPI:", exc_info=True)
