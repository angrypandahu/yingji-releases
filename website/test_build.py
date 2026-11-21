import hashlib
from io import BytesIO
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import build


def release(tag, *platforms):
    assets = []
    for platform in platforms:
        name = f"Yingji-{tag[1:]}-{build.SUFFIX[platform]}"
        data = name.encode()
        assets.append(dict(name=name, size=len(data), digest="sha256:" + hashlib.sha256(data).hexdigest()))
    return dict(tagName=tag, isDraft=False, isPrerelease=False, assets=assets)


class WebsiteReleaseTest(unittest.TestCase):
    def setUp(self):
        self.site = dict(base_url="https://oss.example", repo="owner/releases",
                         icon="icon", demos=dict.fromkeys(("feishu_chat", "feishu_note", "collections"), "demo"),
                         downloads={})
        self.missing = set()

        def request(site, name, method="GET"):
            if name in self.missing:
                raise HTTPError(name, 404, "not found", {}, None)
            response = BytesIO(name.encode())
            response.headers = {"Content-Length": str(len(name.encode()))}
            return response

        mock = patch.object(build, "oss_request", side_effect=request)
        mock.start()
        self.addCleanup(mock.stop)
        build.apply_release(self.site, release("v0.1.14", "mac"))

    def page(self):
        return build.render(self.site, (build.ROOT / "template.html").read_text(), check=True)

    def test_late_windows_and_independent_platforms(self):
        exe = "Yingji-0.1.15-Windows-x64.exe"
        pair = release("v0.1.15", "mac", "windows")
        self.missing.add(exe)
        build.apply_release(self.site, pair)
        self.assertIn("Yingji-0.1.15-macOS-arm64.dmg", self.page())
        self.assertNotIn("Windows", self.page())
        self.missing.clear()
        build.apply_release(self.site, release("v0.1.15", "windows"))
        build.apply_release(self.site, release("v0.1.16", "mac"))
        build.apply_release(self.site, release("v0.1.14", "mac", "windows"))
        page = self.page()
        self.assertIn("Yingji-0.1.16-macOS-arm64.dmg", page)
        self.assertIn('href="https://oss.example/' + exe + '"', page)
        self.assertIn('releases/tag/v0.1.15">Windows', page)
        self.missing.add("Yingji-0.1.17-Windows-x64.exe")
        build.apply_release(self.site, release("v0.1.17", "windows"))
        self.assertIn(exe, self.page())
        self.missing.add(exe)
        self.assertNotIn("下载 Windows 版", self.page())

    def test_reject_untrusted_release_or_mismatched_file(self):
        data = release("v0.1.15", "windows")
        for flag in ("isDraft", "isPrerelease"):
            with self.assertRaises(ValueError):
                build.apply_release(self.site, {**data, flag: True})
        data["assets"][0]["digest"] = "sha256:wrong"
        with self.assertRaises(ValueError):
            build.apply_release(self.site, data)
        self.assertNotIn("windows", self.site["downloads"])
