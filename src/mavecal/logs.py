"""Logging set-up shared by the workflow scripts."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(path: str | Path, name: str = "mavecal") -> logging.Logger:
    """Write timestamped records to the rule's log file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(path),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    logging.captureWarnings(True)
    # Tracebacks go to stderr; send them to the rule log so a failed job explains itself.
    sys.stderr = open(path, "a", buffering=1)  # noqa: SIM115
    return logging.getLogger(name)
