import functools
import http.server
import json
import os
import pathlib
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = (
    ("firefox-320x533", {"width": 320, "height": 533}),
    ("firefox-393x727", {"width": 393, "height": 727}),
    ("firefox-539x980", {"width": 539, "height": 980}),
    ("firefox-800x1280", {"width": 800, "height": 1280}),
    ("firefox-1366x768", {"width": 1366, "height": 768}),
)
HERO_KEYFRAMES = (0, 28, 36, 49, 57, 68, 100)


class FirefoxPostalProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.firefox.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_postal_story_across_firefox_profiles(self):
        shard_index = int(os.environ.get("VISUAL_TEST_SHARD_INDEX", "0"))
        shard_count = int(os.environ.get("VISUAL_TEST_SHARD_COUNT", "1"))
        artifact_root = ROOT / "test-artifacts" / "firefox"
        artifact_root.mkdir(parents=True, exist_ok=True)
        manifest_profiles = []

        for profile_index, (name, viewport) in enumerate(PROFILES):
            if profile_index % shard_count != shard_index:
                continue

            profile_dir = artifact_root / f"{profile_index + 1:02d}-{viewport['width']}x{viewport['height']}"
            profile_dir.mkdir(parents=True, exist_ok=True)
            context = self.browser.new_context(viewport=viewport)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            page.goto(self.base_url, wait_until="networkidle")
            page.add_style_tag(content=".skip-link,.reading-progress{display:none!important}")

            screenshot_paths = {}
            minimum_label_inset = float("inf")
            for percent in HERO_KEYFRAMES:
                page.evaluate(
                    """time => {
                      const root = document.querySelector('.post-office');
                      root.getAnimations({subtree: true}).forEach(animation => {
                        animation.pause();
                        animation.currentTime = time;
                      });
                    }""",
                    5500 * percent / 100,
                )
                containment = page.locator(".letter-sheet").evaluate(
                    """element => {
                      const sheet = element.getBoundingClientRect();
                      const label = element.querySelector('b').getBoundingClientRect();
                      return {
                        left: label.left - sheet.left,
                        right: sheet.right - label.right,
                      };
                    }"""
                )
                self.assertGreaterEqual(containment["left"], 2, f"{name} hero {percent}%: label escapes left")
                self.assertGreaterEqual(containment["right"], 2, f"{name} hero {percent}%: label escapes right")
                minimum_label_inset = min(minimum_label_inset, containment["left"], containment["right"])
                destination = profile_dir / f"01-hero-{percent:03d}.png"
                page.locator(".post-office").screenshot(path=str(destination))
                screenshot_paths[f"hero_{percent:03d}"] = str(destination.relative_to(ROOT))

            page.locator("#posta").scroll_into_view_if_needed()
            postal_map = page.locator(".postal-map")
            postal_map.scroll_into_view_if_needed()
            page.locator(".postal-map.is-visible").wait_for(state="visible")
            self.assertEqual(postal_map.locator(":scope > div").count(), 7)
            self.assertLessEqual(
                postal_map.evaluate("element => element.scrollWidth - element.clientWidth"),
                1,
                f"{name}: postal map overflows",
            )
            if viewport["width"] <= 820:
                glossary_sizes = postal_map.locator("dt, dd").evaluate_all(
                    "elements => elements.map(element => parseFloat(getComputedStyle(element).fontSize))"
                )
                self.assertGreaterEqual(min(glossary_sizes), 15, f"{name}: glossary text is below 15px")
            map_destination = profile_dir / "02-postal-map.png"
            postal_map.screenshot(path=str(map_destination), animations="disabled")
            screenshot_paths["postal_map"] = str(map_destination.relative_to(ROOT))

            story = page.locator("mail-story")
            story.scroll_into_view_if_needed()
            page.locator("mail-story.is-visible").wait_for(state="visible")
            story.locator('[data-step="1"]').evaluate("button => button.click()")
            story.locator(".mail-note-cipher").wait_for(state="attached")
            page.evaluate(
                """() => {
                  const root = document.querySelector('mail-story .mail-illustration');
                  root.getAnimations({subtree: true}).forEach(animation => {
                    animation.pause();
                    animation.currentTime = 4600;
                  });
                }"""
            )
            self.assertEqual(story.locator(".mail-e2ee-key-traveller").count(), 0)
            self.assertEqual(story.locator(".mail-note-cipher").evaluate("element => getComputedStyle(element).opacity"), "1")
            self.assertEqual(story.locator(".mail-note-plain").evaluate("element => getComputedStyle(element).opacity"), "0")
            self.assertEqual(story.locator(".mail-lock").evaluate("element => getComputedStyle(element).opacity"), "1")
            self.assertIn("nem kerül", story.locator(".mail-e2ee-key small").inner_text())
            postman_box = story.locator(".mail-postman").bounding_box()
            key_box = story.locator(".mail-e2ee-key").bounding_box()
            object_box = story.locator(".mail-object").bounding_box()
            overlap_width = max(
                0,
                min(postman_box["x"] + postman_box["width"], key_box["x"] + key_box["width"])
                - max(postman_box["x"], key_box["x"]),
            )
            overlap_height = max(
                0,
                min(postman_box["y"] + postman_box["height"], key_box["y"] + key_box["height"])
                - max(postman_box["y"], key_box["y"]),
            )
            self.assertLessEqual(overlap_width * overlap_height, 1, f"{name}: recipient-key card covers postman")
            object_overlap_width = max(
                0,
                min(object_box["x"] + object_box["width"], key_box["x"] + key_box["width"])
                - max(object_box["x"], key_box["x"]),
            )
            object_overlap_height = max(
                0,
                min(object_box["y"] + object_box["height"], key_box["y"] + key_box["height"])
                - max(object_box["y"], key_box["y"]),
            )
            self.assertLessEqual(
                object_overlap_width * object_overlap_height,
                1,
                f"{name}: recipient-key card covers locked envelope",
            )
            recipient_destination = profile_dir / "03-recipient-key-stays.png"
            story.locator(".mail-illustration").screenshot(path=str(recipient_destination))
            screenshot_paths["recipient_key_stays"] = str(recipient_destination.relative_to(ROOT))

            encryption = page.locator("encryption-layers")
            expected_keys = {
                "1 · Két zárt útszakasz": ("1. kapcsolat kulcsa", "1. és 2. kapcsolat kulcsa", "2. kapcsolat kulcsa"),
                "2 · A raktáros kulcsa": ("Tárolási kulcs",),
                "3 · A kulcs nálad marad": ("Fájlkulcs",),
                "4 · Lezárva a címzettig": ("Beszélgetés kulcsa", "Beszélgetés kulcsa"),
            }
            for mode_index, (tab_name, key_labels) in enumerate(expected_keys.items(), start=1):
                encryption.get_by_role("tab", name=tab_name).click()
                self.assertEqual(encryption.locator(".story-key").all_inner_texts(), list(key_labels), name)
                self.assertEqual(encryption.locator(".provider-window small").text_content(), "Mit lát a szolgáltató?")
                self.assertLessEqual(
                    encryption.locator(".encryption-panel").evaluate("element => element.scrollWidth - element.clientWidth"),
                    1,
                    f"{name}: encryption mode {mode_index} overflows",
                )
                mode_destination = profile_dir / f"04-encryption-{mode_index}.png"
                encryption.locator(".encryption-panel").screenshot(path=str(mode_destination), animations="disabled")
                screenshot_paths[f"encryption_{mode_index}"] = str(mode_destination.relative_to(ROOT))

            horizontal_overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            self.assertLessEqual(horizontal_overflow, 1, name)
            self.assertEqual(errors, [], name)
            manifest_profiles.append(
                {
                    "profile_index": profile_index,
                    "name": name,
                    "viewport": viewport,
                    "screenshots": screenshot_paths,
                    "metrics": {
                        "minimum_hero_label_inset_px": round(minimum_label_inset, 2),
                        "horizontal_overflow_px": horizontal_overflow,
                        "browser_errors": errors,
                    },
                }
            )
            context.close()

        manifest = {
            "description": "Firefox postal-metaphor and animation regression profiles",
            "total_profile_count": len(PROFILES),
            "shard_index": shard_index,
            "shard_count": shard_count,
            "profiles": manifest_profiles,
        }
        manifest_path = artifact_root / f"manifest-shard-{shard_index + 1}-of-{shard_count}.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
