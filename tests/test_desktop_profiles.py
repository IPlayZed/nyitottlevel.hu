import functools
import http.server
import json
import os
import pathlib
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHROMIUM = "/usr/bin/chromium-browser"
VIEWPORTS = (
    ("small-laptop", 1024, 768),
    ("common-laptop", 1366, 768),
    ("large-laptop", 1440, 900),
    ("full-hd", 1920, 1080),
    ("qhd", 2560, 1440),
)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class ChromiumDesktopProfileTests(unittest.TestCase):
    """Capture and analyse the documented desktop support matrix."""

    @classmethod
    def setUpClass(cls):
        handler = functools.partial(QuietHandler, directory=ROOT)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=CHROMIUM,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        cls.artifact_root = ROOT / "test-artifacts" / "desktop"
        cls.artifact_root.mkdir(parents=True, exist_ok=True)
        cls.total_profile_count = len(VIEWPORTS)
        cls.shard_count = max(1, int(os.environ.get("VISUAL_TEST_SHARD_COUNT", "1")))
        cls.shard_index = int(os.environ.get("VISUAL_TEST_SHARD_INDEX", "0"))
        if not 0 <= cls.shard_index < cls.shard_count:
            raise ValueError("VISUAL_TEST_SHARD_INDEX must be between 0 and VISUAL_TEST_SHARD_COUNT - 1")
        cls.viewports = [
            (profile_index, viewport)
            for profile_index, viewport in enumerate(VIEWPORTS, start=1)
            if (profile_index - 1) % cls.shard_count == cls.shard_index
        ]
        cls.manifest = []

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        manifest_name = (
            "manifest.json"
            if cls.shard_count == 1
            else f"manifest-shard-{cls.shard_index + 1}-of-{cls.shard_count}.json"
        )
        destination = cls.artifact_root / manifest_name
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "description": "Stateful screenshots and geometry analysis for the desktop support matrix",
                    "profile_count": len(cls.manifest),
                    "total_profile_count": cls.total_profile_count,
                    "shard_index": cls.shard_index,
                    "shard_count": cls.shard_count,
                    "profiles": cls.manifest,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(destination)

    def assert_inside(self, inner, outer, label, tolerance=1.5):
        self.assertGreaterEqual(inner["x"], outer["x"] - tolerance, f"{label} escapes left")
        self.assertLessEqual(
            inner["x"] + inner["width"],
            outer["x"] + outer["width"] + tolerance,
            f"{label} escapes right",
        )

    def test_desktop_support_matrix_with_clicked_and_scrolled_states(self):
        for profile_index, (name, width, height) in self.viewports:
            with self.subTest(profile=name):
                context = self.browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                artifact_dir = self.artifact_root / f"{width}x{height}"
                artifact_dir.mkdir(parents=True, exist_ok=True)
                try:
                    page.goto(self.base_url, wait_until="networkidle")
                    page.add_style_tag(content=".skip-link,.reading-progress{display:none!important}")
                    screenshots = {}

                    def capture(key, filename, selector=None):
                        path = artifact_dir / filename
                        if selector:
                            page.locator(selector).screenshot(path=str(path), type="jpeg", quality=62)
                        else:
                            page.screenshot(path=str(path), type="jpeg", quality=62)
                        screenshots[key] = str(path.relative_to(ROOT))

                    capture("top", "01-top.jpg")
                    page.evaluate("""() => {
                      const letter = document.querySelector('.moving-letter');
                      const postman = document.querySelector('.hero-postman');
                      [...letter.querySelectorAll('*'), letter, postman, ...postman.querySelectorAll('*')]
                        .forEach(element => { element.style.animation = 'none'; });
                      letter.style.transform = 'translateX(32px) rotate(-1deg)';
                      letter.querySelector('.letter-flap').style.transform = 'scaleY(-1)';
                      letter.querySelector('.letter-sheet').style.transform = 'translateY(-31px)';
                      letter.querySelector('.letter-heart').style.opacity = '0';
                      postman.style.transform = 'translateX(92px) translateY(-2px) scale(.8)';
                      postman.querySelector('.postman-arm--front').style.transform = 'rotate(-96deg) translateY(-2px)';
                    }""")
                    capture("hero_mail_open", "02-hero-mail-open.jpg", ".post-office")
                    letter_box = page.locator(".moving-letter").bounding_box()
                    sheet_box = page.locator(".letter-sheet").bounding_box()
                    self.assertLess(sheet_box["y"], letter_box["y"], name)
                    self.assertEqual(page.locator(".letter-seal").count(), 0)
                    page.locator("#motionToggle").click()
                    capture("paused_header", "02-paused-header.jpg", ".site-header")
                    capture("action_cards", "03-action-cards.jpg", ".action-grid")

                    page.locator('mail-story [data-step="1"]').click()
                    page.evaluate("""phase => {
                      const story = document.querySelector('mail-story');
                      story.querySelectorAll('*').forEach(element => { element.style.animation = 'none'; });
                      story.querySelector('.mail-e2ee-no-key').style.opacity = phase === 'no-key' ? '1' : '0';
                      const keyCard = story.querySelector('.mail-e2ee-key');
                      keyCard.style.opacity = phase === 'recipient-key' ? '1' : '0';
                      keyCard.style.transform = 'none';
                      story.querySelector('.mail-e2ee-key-traveller').style.opacity = '0';
                    }""", "no-key")
                    capture("mail_no_key", "04-mail-no-key.jpg", "mail-story .interactive-card")
                    page.evaluate("""() => {
                      const story = document.querySelector('mail-story');
                      story.querySelector('.mail-e2ee-no-key').style.opacity = '0';
                      story.querySelector('.mail-e2ee-key').style.opacity = '1';
                    }""")
                    capture("mail_recipient_key", "05-mail-recipient-key.jpg", "mail-story .interactive-card")

                    encryption_label_margins = []
                    encryption_captures = {
                        "https": ("transport_encryption", "06a-transport-encryption.jpg"),
                        "providerRest": ("provider_key_encryption", "06b-provider-key-encryption.jpg"),
                        "userRest": ("user_key_encryption", "06c-user-key-encryption.jpg"),
                        "e2ee": ("e2ee_encryption", "06d-e2ee-encryption.jpg"),
                    }
                    for mode, (key, filename) in encryption_captures.items():
                        page.locator(f'encryption-layers [data-encryption="{mode}"]').click()
                        capture(key, filename, "encryption-layers .encryption-shell")
                        diagram = page.locator("encryption-layers .crypto-diagram").bounding_box()
                        labels = page.locator(
                            "encryption-layers .crypto-packet:visible, "
                            "encryption-layers .crypto-key-chip:visible, "
                            "encryption-layers .crypto-access-state:visible"
                        )
                        for index, label in enumerate(labels.all()):
                            label_box = label.bounding_box()
                            self.assert_inside(label_box, diagram, f"{name}: {mode} diagram label {index + 1}")
                            encryption_label_margins.append(round(min(
                                label_box["x"] - diagram["x"],
                                diagram["x"] + diagram["width"] - label_box["x"] - label_box["width"],
                            ), 2))
                        graphics = page.locator(
                            "encryption-layers .crypto-device:visible, "
                            "encryption-layers .crypto-server:visible, "
                            "encryption-layers .crypto-database:visible"
                        )
                        for index, graphic in enumerate(graphics.all()):
                            graphic_box = graphic.bounding_box()
                            self.assertGreaterEqual(
                                graphic_box["x"],
                                diagram["x"] + 6,
                                f"{name}: {mode} graphic {index + 1} lacks left shadow clearance",
                            )
                            self.assertLessEqual(
                                graphic_box["x"] + graphic_box["width"],
                                diagram["x"] + diagram["width"] - 6,
                                f"{name}: {mode} graphic {index + 1} lacks right shadow clearance",
                            )
                        states = [
                            state.bounding_box()
                            for state in page.locator("encryption-layers .crypto-access-state:visible").all()
                        ]
                        if len(states) == 2:
                            first, second = states
                            separated = (
                                first["x"] + first["width"] <= second["x"]
                                or second["x"] + second["width"] <= first["x"]
                                or first["y"] + first["height"] <= second["y"]
                                or second["y"] + second["height"] <= first["y"]
                            )
                            self.assertTrue(separated, f"{name}: {mode} access-state chips overlap")
                    capture("rare_results", "07-rare-results.jpg", "detection-lab .rate-magnifier")
                    page.locator('surveillance-contrast [data-surveillance="mass"]').click()
                    capture("mass_surveillance", "08-mass-surveillance.jpg", "surveillance-contrast .surveillance-shell")
                    page.locator('[data-connection-filter="help"]').click()
                    capture("help_directory", "09-help-directory.jpg", "#kapcsolodas .connection-explorer")
                    capture("vote_explorer", "10-vote-explorer.jpg", "vote-explorer .vote-explorer-shell")
                    capture("safeguards", "11-safeguards.jpg", "safeguard-builder .safeguard-shell")

                    action_gaps = []
                    for card in page.locator(".action-grid article").all():
                        paragraph = card.locator("p").bounding_box()
                        action = card.locator(".card-button").bounding_box()
                        action_gaps.append(action["y"] - paragraph["y"] - paragraph["height"])
                    helper_sizes = page.eval_on_selector_all(
                        ".mail-e2ee-no-key span, .mail-e2ee-key small, .mail-key-comparison small, .surveillance-facts dd, .connection-grid p, footer p",
                        "elements => elements.map(element => parseFloat(getComputedStyle(element).fontSize))",
                    )
                    overflow = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
                    self.assertGreaterEqual(min(helper_sizes), 14, name)
                    self.assertGreaterEqual(min(action_gaps), 12, name)
                    self.assertLessEqual(overflow, 1, name)
                    self.assertEqual(errors, [], name)
                    self.assertEqual(page.locator("#kapcsolodas [data-connection-card]:visible").count(), 6)
                    self.manifest.append(
                        {
                            "profile_index": profile_index,
                            "name": name,
                            "viewport": {"width": width, "height": height},
                            "screenshots": screenshots,
                            "analysis": {
                                "horizontal_overflow_px": overflow,
                                "minimum_action_copy_to_button_gap_px": round(min(action_gaps), 2),
                                "minimum_readable_helper_font_px": min(helper_sizes),
                                "minimum_encryption_label_edge_margin_px": min(encryption_label_margins),
                                "opened_letter_sheet_rise_px": round(letter_box["y"] - sheet_box["y"], 2),
                                "browser_errors": errors,
                            },
                            "screenshot_bytes": {
                                key: (ROOT / path).stat().st_size for key, path in screenshots.items()
                            },
                        }
                    )
                finally:
                    context.close()


if __name__ == "__main__":
    unittest.main()
