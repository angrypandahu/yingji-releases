#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent


def url(base, name):
    return f"{base.rstrip('/')}/{name}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--download", help="calculate size and sha256 from a local DMG")
    args = parser.parse_args()
    site = json.loads((ROOT / "site.json").read_text())
    if args.download:
        path = Path(args.download)
        site["file"] = path.name
        site["size"] = f"{path.stat().st_size / 1024 / 1024:.0f}MB"
        site["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()

    release_url = f"https://github.com/{site['repo']}/releases/tag/{site['version']}"
    values = {
        "version": site["version"],
        "download_url": url(site["base_url"], site["file"]),
        "size": site["size"],
        "release_url": release_url,
        "icon": url(site["base_url"], site["icon"]),
        "feishu_chat": url(site["base_url"], site["demos"]["feishu_chat"]),
        "feishu_note": url(site["base_url"], site["demos"]["feishu_note"]),
        "collections": url(site["base_url"], site["demos"]["collections"]),
    }
    template = (ROOT / "template.html").read_text()
    page = re.sub(r"\{\{(\w+)\}\}", lambda match: values[match.group(1)], template)

    if args.check:
        asset_keys = ("icon", "feishu_chat", "feishu_note", "collections")
        for link in [values["download_url"], *(values[key] for key in asset_keys)]:
            parsed = urlparse(link)
            assert parsed.scheme == "https" and parsed.hostname, link
            with urlopen(Request(link, method="HEAD"), timeout=30) as response:
                assert response.status == 200, (link, response.status)
        assert site["sha256"], "missing sha256"

    (ROOT / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "index.html").write_text(page)


if __name__ == "__main__":
    main()
