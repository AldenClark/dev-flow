#!/usr/bin/env python3
"""Backward-compatible packet validator wrapper."""

from __future__ import annotations

import sys

from dev_flow import main


if __name__ == "__main__":
    sys.exit(main(["validate-packet", *sys.argv[1:]]))
