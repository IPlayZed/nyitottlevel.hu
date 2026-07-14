import functools
import http.server
import json
import pathlib
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHROMIUM = "/usr/bin/chromium-browser"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class ChromiumMobileProfileTests(unittest.TestCase):
    """Exercise every unique viewport in Playwright's built-in Chromium mobile catalogue."""

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

        profiles_by_size = {}
        for name, descriptor in cls.playwright.devices.items():
            if not descriptor.get("is_mobile") or descriptor.get("default_browser_type") != "chromium":
                continue
            viewport = descriptor["viewport"]
            size = (viewport["width"], viewport["height"])
            profiles_by_size.setdefault(size, (name, descriptor))
        cls.profiles = [profiles_by_size[size] for size in sorted(profiles_by_size)]
        cls.artifact_root = ROOT / "test-artifacts" / "mobile"
        cls.artifact_root.mkdir(parents=True, exist_ok=True)
        cls.artifact_manifest = []

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        manifest = {
            "description": "Interactive screenshots and geometry analysis for every unique built-in Chromium mobile viewport",
            "profile_count": len(cls.profiles),
            "profiles": cls.artifact_manifest,
        }
        (cls.artifact_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def assert_inside(self, inner, outer, label, tolerance=1.5):
        self.assertGreaterEqual(inner["x"], outer["x"] - tolerance, f"{label} escapes left")
        self.assertLessEqual(
            inner["x"] + inner["width"],
            outer["x"] + outer["width"] + tolerance,
            f"{label} escapes right",
        )

    def test_all_builtin_chromium_mobile_viewport_sizes_interactively(self):
        self.assertGreaterEqual(len(self.profiles), 50)
        for profile_index, (name, raw_descriptor) in enumerate(self.profiles, start=1):
            descriptor = {key: value for key, value in raw_descriptor.items() if key != "default_browser_type"}
            viewport = descriptor["viewport"]
            profile_label = f"{name} ({viewport['width']}×{viewport['height']})"
            artifact_id = f"{profile_index:02d}-{viewport['width']}x{viewport['height']}"
            artifact_dir = self.artifact_root / artifact_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            with self.subTest(profile=profile_label):
                context = self.browser.new_context(**descriptor)
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
                try:
                    page.goto(self.base_url, wait_until="domcontentloaded")
                    screenshot_paths = {}

                    top_path = artifact_dir / "01-top.jpg"
                    page.screenshot(path=str(top_path), type="jpeg", quality=58)
                    screenshot_paths["top"] = str(top_path.relative_to(ROOT))

                    motion = page.locator("#motionToggle")
                    self.assertTrue(motion.is_visible(), profile_label)
                    self.assertEqual(motion.locator(".button-label").inner_text(), "Animáció leállítása")
                    motion.click()
                    self.assertEqual(motion.get_attribute("aria-pressed"), "true")
                    self.assertEqual(motion.locator(".button-label").inner_text(), "Animáció indítása")

                    menu = page.locator("#menuButton")
                    if menu.is_visible():
                        menu.click()
                        self.assertTrue(page.locator("#mobileNav").is_visible(), profile_label)
                        menu.click()
                    else:
                        self.assertTrue(page.locator(".desktop-nav").is_visible(), profile_label)

                    header_path = artifact_dir / "02-header-motion-paused.jpg"
                    page.locator(".site-header").screenshot(path=str(header_path), type="jpeg", quality=65)
                    screenshot_paths["header_motion_paused"] = str(header_path.relative_to(ROOT))

                    header_box = page.locator(".site-header").bounding_box()
                    self.assert_inside(motion.bounding_box(), header_box, f"{profile_label}: motion control")
                    if menu.is_visible():
                        self.assert_inside(menu.bounding_box(), header_box, f"{profile_label}: menu")

                    action_gaps = []
                    for index, card in enumerate(page.locator(".action-grid article").all()):
                        paragraph_box = card.locator("p").bounding_box()
                        button_box = card.locator(".card-button").bounding_box()
                        action_gap = button_box["y"] - paragraph_box["y"] - paragraph_box["height"]
                        action_gaps.append(round(action_gap, 2))
                        self.assertGreaterEqual(
                            button_box["y"],
                            paragraph_box["y"] + paragraph_box["height"] + 12,
                            f"{profile_label}: action card {index + 1} copy overlaps its action",
                        )
                    action_path = artifact_dir / "03-action-cards.jpg"
                    page.locator(".action-grid").screenshot(path=str(action_path), type="jpeg", quality=58)
                    screenshot_paths["action_cards"] = str(action_path.relative_to(ROOT))

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
                    no_key_path = artifact_dir / "04-mail-no-key.jpg"
                    page.locator("mail-story .interactive-card").screenshot(path=str(no_key_path), type="jpeg", quality=58)
                    screenshot_paths["mail_no_key"] = str(no_key_path.relative_to(ROOT))
                    page.evaluate("""() => {
                      const story = document.querySelector('mail-story');
                      story.querySelector('.mail-e2ee-no-key').style.opacity = '0';
                      story.querySelector('.mail-e2ee-key').style.opacity = '1';
                    }""")
                    illustration = page.locator("mail-story .mail-illustration").bounding_box()
                    key_card = page.locator("mail-story .mail-e2ee-key")
                    self.assert_inside(key_card.bounding_box(), illustration, f"{profile_label}: recipient key card")
                    icon_box = key_card.locator(":scope > i").bounding_box()
                    text_box = key_card.locator(":scope > span").bounding_box()
                    self.assertLessEqual(
                        icon_box["x"] + 55,
                        text_box["x"] + 1,
                        f"{profile_label}: key drawing overlaps recipient-key text",
                    )
                    key_clearance = text_box["x"] - (icon_box["x"] + 55)
                    mail_path = artifact_dir / "05-mail-recipient-key.jpg"
                    page.locator("mail-story .interactive-card").screenshot(path=str(mail_path), type="jpeg", quality=58)
                    screenshot_paths["mail_recipient_key"] = str(mail_path.relative_to(ROOT))

                    page.locator('encryption-layers [data-encryption="userRest"]').click()
                    diagram = page.locator("encryption-layers .crypto-diagram").bounding_box()
                    route_margins = []
                    for index, packet in enumerate(page.locator("encryption-layers .crypto-packet").all()):
                        packet_box = packet.bounding_box()
                        self.assert_inside(packet_box, diagram, f"{profile_label}: route label {index + 1}")
                        route_margins.append(round(min(
                            packet_box["x"] - diagram["x"],
                            diagram["x"] + diagram["width"] - packet_box["x"] - packet_box["width"],
                        ), 2))
                    encryption_path = artifact_dir / "06-encryption-user-key.jpg"
                    page.locator("encryption-layers .encryption-shell").screenshot(path=str(encryption_path), type="jpeg", quality=58)
                    screenshot_paths["encryption_user_key"] = str(encryption_path.relative_to(ROOT))

                    magnifier_path = artifact_dir / "07-rare-result-magnifier.jpg"
                    page.locator("detection-lab .rate-magnifier").screenshot(path=str(magnifier_path), type="jpeg", quality=62)
                    screenshot_paths["rare_result_magnifier"] = str(magnifier_path.relative_to(ROOT))

                    page.locator('surveillance-contrast [data-surveillance="mass"]').click()
                    mass_path = artifact_dir / "08-mass-surveillance.jpg"
                    page.locator("surveillance-contrast .surveillance-shell").screenshot(path=str(mass_path), type="jpeg", quality=58)
                    screenshot_paths["mass_surveillance"] = str(mass_path.relative_to(ROOT))
                    self.assertEqual(page.locator("surveillance-contrast .surveillance-person.is-flagged").count(), 3)

                    page.locator('[data-connection-filter="help"]').click()
                    connection_path = artifact_dir / "09-help-directory.jpg"
                    page.locator("#kapcsolodas .connection-explorer").screenshot(path=str(connection_path), type="jpeg", quality=58)
                    screenshot_paths["help_directory"] = str(connection_path.relative_to(ROOT))
                    visible_connection_cards = page.locator("#kapcsolodas [data-connection-card]:visible").count()
                    self.assertEqual(visible_connection_cards, 6)

                    readable_selector = ",".join((
                        ".mail-e2ee-no-key b", ".mail-e2ee-no-key span", ".mail-e2ee-key b",
                        ".mail-e2ee-key small", ".mail-key-comparison span", ".mail-key-comparison small",
                        ".rate-results span", ".rate-derived small", ".rare-count > span", "footer p",
                        ".surveillance-facts dd", ".surveillance-caveat", ".connection-grid p",
                    ))
                    readable_sizes = page.eval_on_selector_all(
                        readable_selector,
                        "elements => elements.map(element => parseFloat(getComputedStyle(element).fontSize))",
                    )
                    expected_readable_floor = 15 if viewport["width"] <= 820 else 14
                    self.assertGreaterEqual(min(readable_sizes), expected_readable_floor, profile_label)
                    diagram_sizes = page.eval_on_selector_all(
                        ".crypto-packet b, .crypto-key-chip, .crypto-access-state",
                        "elements => elements.map(element => parseFloat(getComputedStyle(element).fontSize))",
                    )
                    expected_diagram_floor = 14 if viewport["width"] <= 820 else 13
                    self.assertGreaterEqual(min(diagram_sizes), expected_diagram_floor, profile_label)

                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    )
                    overflow_sources = page.evaluate("""() => [...document.querySelectorAll('body *')]
                      .map(element => ({
                        tag: element.tagName.toLowerCase(),
                        className: typeof element.className === 'string' ? element.className : '',
                        left: element.getBoundingClientRect().left,
                        right: element.getBoundingClientRect().right,
                      }))
                      .filter(item => item.right > innerWidth + 1 || item.left < -1)
                      .sort((a, b) => Math.max(b.right - innerWidth, -b.left) - Math.max(a.right - innerWidth, -a.left))
                      .slice(0, 8)""")
                    self.assertLessEqual(
                        overflow,
                        1,
                        f"{profile_label}: horizontal overflow {overflow}px from {overflow_sources}",
                    )
                    self.assertEqual(errors, [], f"{profile_label}: browser errors {errors}")
                    self.artifact_manifest.append({
                        "name": name,
                        "viewport": viewport,
                        "screenshots": screenshot_paths,
                        "analysis": {
                            "horizontal_overflow_px": overflow,
                            "minimum_action_copy_to_button_gap_px": min(action_gaps),
                            "recipient_key_clearance_px": round(key_clearance, 2),
                            "minimum_route_label_edge_margin_px": min(route_margins),
                            "minimum_readable_helper_font_px": min(readable_sizes),
                            "minimum_diagram_label_font_px": min(diagram_sizes),
                            "visible_help_directory_cards": visible_connection_cards,
                            "horizontal_overflow_sources": overflow_sources,
                            "browser_errors": errors,
                        },
                        "screenshot_bytes": {
                            key: (ROOT / path).stat().st_size for key, path in screenshot_paths.items()
                        },
                    })
                finally:
                    context.close()


if __name__ == "__main__":
    unittest.main()
