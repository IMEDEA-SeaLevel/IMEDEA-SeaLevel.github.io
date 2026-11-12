"""Shared helpers for the site scripts."""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
USER_AGENT = "imedea-sealevel-site/1.0 (+https://imedea-sealevel.github.io)"


def load(name):
    path = DATA / name
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump(name, obj, header):
    text = "# " + header + "\n" + yaml.safe_dump(
        obj, allow_unicode=True, sort_keys=False, width=100, default_flow_style=False
    )
    path = DATA / name
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != text:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def get_json(url, headers=None, retries=4):
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    hdrs.update(headers or {})
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def norm(s):
    """Normalise a grant reference: upper-case, letters and digits only."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def norm_doi(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s)
    return s


def norm_orcid(s):
    m = re.search(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", str(s or "").upper())
    return m.group(0) if m else ""


def env(name):
    return os.environ.get(name, "").strip()
