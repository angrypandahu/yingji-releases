#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
SUFFIX = {"mac": "macOS-arm64.dmg", "windows": "Windows-x64.exe"}


def version(tag):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"无效的稳定版本 {tag}")
    return tuple(map(int, tag[1:].split(".")))


def oss_request(site, file, method="GET"):
    return urlopen(Request(f"{site['base_url']}/{file}", method=method), timeout=60)


def digest(stream):
    hasher = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        size += len(block)
        hasher.update(block)
    return size, hasher.hexdigest()


def apply_release(site, release):
    tag = release["tagName"]
    target = version(tag)
    if release["isDraft"] or release["isPrerelease"]:
        raise ValueError("只能部署已公开的稳定版本")
    assets = {asset["name"]: asset for asset in release["assets"]}
    for platform, suffix in SUFFIX.items():
        name = f"Yingji-{tag[1:]}-{suffix}"
        asset = assets.get(name)
        current = site["downloads"].get(platform)
        if not asset or (current and target < version(current["version"])):
            continue
        try:
            with oss_request(site, name) as response:
                size, sha = digest(response)
        except HTTPError as error:
            if platform == "windows" and error.code in (403, 404):
                print(f"Windows 安装包尚未开放下载 (HTTP {error.code}): {name}")
                continue
            raise
        if not size or size != asset["size"] or f"sha256:{sha}" != asset["digest"]:
            raise ValueError(f"OSS 与 Release 的安装包不一致: {name}")
        record = dict(version=tag, file=name, bytes=size, sha256=sha)
        if current and current["version"] == tag and current != record:
            raise ValueError(f"同名安装包内容发生变化: {name}")
        site["downloads"][platform] = record


def render(site, template, check=False):
    downloads = site["downloads"]
    windows = downloads.get("windows")
    if check:
        for platform, item in downloads.items():
            try:
                with oss_request(site, item["file"], "HEAD") as response:
                    if int(response.headers["Content-Length"]) != item["bytes"]:
                        raise ValueError(f"OSS 文件大小不一致: {item['file']}")
            except HTTPError as error:
                if platform != "windows" or error.code not in (403, 404):
                    raise
                windows = None
        for file in (site["icon"], *site["demos"].values()):
            with oss_request(site, file, "HEAD"):
                pass
    template = re.sub(r"{{#windows}}(.*?){{/windows}}",
                      r"\1" if windows else "", template, flags=re.S)
    base = site["base_url"]
    values = {key: f"{base}/{file}" for key, file in site["demos"].items()}
    values["icon"] = f"{base}/{site['icon']}"
    for prefix, item in (("", downloads["mac"]), ("windows_", windows)):
        if item:
            values.update({
                prefix + "version": item["version"],
                prefix + "download_url": f"{base}/{item['file']}",
                prefix + "size": f"{item['bytes'] / 1024**2:.0f}MB",
                prefix + "release_url": f"https://github.com/{site['repo']}/releases/tag/{item['version']}",
            })
    return re.sub(r"{{(\w+)}}", lambda m: values[m[1]], template)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--release", type=Path, help="gh release view JSON")
    inputs.add_argument("--download", type=Path, help="本地 Mac DMG")
    args = parser.parse_args()
    site = json.loads((ROOT / "site.json").read_text())
    if args.release:
        apply_release(site, json.loads(args.release.read_text()))
    if args.download:
        mac = site["downloads"]["mac"]
        with args.download.open("rb") as stream:
            size, sha = digest(stream)
        mac.update(file=args.download.name, bytes=size, sha256=sha)
    page = render(site, (ROOT / "template.html").read_text(), args.check)
    (ROOT / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "index.html").write_text(page)


if __name__ == "__main__":
    main()
