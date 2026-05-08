#!/usr/bin/env python3
"""Fetch Chinese Wikipedia summaries for bird species using MediaWiki action=query API."""

import json, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# (full TRAD_TO_SIMP, DIST_RE, CLEAN_RE, read_json, write_json, to_simplified as before; omitted for brevity)
