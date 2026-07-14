import functools
import http.server
import json
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
        cls.manifest = []

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        (cls.artifact_root / "manifest.json").write_text(
            json.dumps(
                {
                    "description": "Stateful screenshots and geometry analysis for the desktop support matrix",
                    "profile_count": len(VIEWPORTS),
                    "profiles": cls.manifest,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_desktop_support_matrix_with_clicked_and_scrolled_states(self):
        for name, width, height in VIEWPORTS:
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
                    screenshots = {}

                    def capture(key, filename, selector=None):
                        path = artifact_dir / filename
                        if selector:
                            page.locator(selector).screenshot(path=str(path), type="jpeg", quality=62)
                        else:
                            page.screenshot(path=str(path), type="jpeg", quality=62)
                        screenshots[key] = str(path.relative_to(ROOT))

                    capture("top", "01-top.jpg")
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

                    page.locator('encryption-layers [data-encryption="userRest"]').click()
                    capture("user_key_encryption", "06-user-key-encryption.jpg", "encryption-layers .encryption-shell")
                    capture("rare_results", "07-rare-results.jpg", "detection-lab .rate-magnifier")
                    page.locator('surveillance-contrast [data-surveillance="mass"]').click()
                    capture("mass_surveillance", "08-mass-surveillance.jpg", "surveillance-contrast .surveillance-shell")
                    page.locator('[data-connection-filter="help"]').click()
                    capture("help_directory", "09-help-directory.jpg", "#kapcsolodas .connection-explorer")

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
                            "name": name,
                            "viewport": {"width": width, "height": height},
                            "screenshots": screenshots,
                            "analysis": {
                                "horizontal_overflow_px": overflow,
                                "minimum_action_copy_to_button_gap_px": round(min(action_gaps), 2),
                                "minimum_readable_helper_font_px": min(helper_sizes),
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
