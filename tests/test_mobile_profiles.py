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
        all_profiles = [profiles_by_size[size] for size in sorted(profiles_by_size)]
        cls.total_profile_count = len(all_profiles)
        cls.shard_count = max(1, int(os.environ.get("VISUAL_TEST_SHARD_COUNT", "1")))
        cls.shard_index = int(os.environ.get("VISUAL_TEST_SHARD_INDEX", "0"))
        if not 0 <= cls.shard_index < cls.shard_count:
            raise ValueError("VISUAL_TEST_SHARD_INDEX must be between 0 and VISUAL_TEST_SHARD_COUNT - 1")
        cls.profiles = [
            (profile_index, name, descriptor)
            for profile_index, (name, descriptor) in enumerate(all_profiles, start=1)
            if (profile_index - 1) % cls.shard_count == cls.shard_index
        ]
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
            "profile_count": len(cls.artifact_manifest),
            "total_profile_count": cls.total_profile_count,
            "shard_index": cls.shard_index,
            "shard_count": cls.shard_count,
            "profiles": cls.artifact_manifest,
        }
        manifest_name = (
            "manifest.json"
            if cls.shard_count == 1
            else f"manifest-shard-{cls.shard_index + 1}-of-{cls.shard_count}.json"
        )
        destination = cls.artifact_root / manifest_name
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
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

    def test_all_builtin_chromium_mobile_viewport_sizes_interactively(self):
        self.assertGreaterEqual(self.total_profile_count, 50)
        for profile_index, name, raw_descriptor in self.profiles:
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
                    page.add_style_tag(content=".skip-link,.reading-progress{display:none!important}")
                    screenshot_paths = {}

                    top_path = artifact_dir / "01-top.jpg"
                    page.screenshot(path=str(top_path), type="jpeg", quality=58)
                    screenshot_paths["top"] = str(top_path.relative_to(ROOT))

                    page.evaluate("""() => {
                      const letter = document.querySelector('.moving-letter');
                      const postman = document.querySelector('.hero-postman');
                      [...letter.querySelectorAll('*'), letter, postman, ...postman.querySelectorAll('*')]
                        .forEach(element => { element.style.animation = 'none'; });
                      const compactHero = innerWidth <= 600;
                      letter.style.transform = compactHero
                        ? 'translateX(48px) scale(.72) rotate(-1deg)'
                        : 'translateX(32px) rotate(-1deg)';
                      letter.querySelector('.letter-flap').style.transform = 'scaleY(-1)';
                      letter.querySelector('.letter-sheet').style.transform = 'translateY(-31px)';
                      letter.querySelector('.letter-heart').style.opacity = '0';
                      postman.style.transform = 'translateX(92px) translateY(-2px) scale(.8)';
                      postman.querySelector('.postman-arm--front').style.transform = 'rotate(-96deg) translateY(-2px)';
                    }""")
                    hero_open_path = artifact_dir / "02-hero-mail-open.jpg"
                    page.locator(".post-office").screenshot(path=str(hero_open_path), type="jpeg", quality=64)
                    screenshot_paths["hero_mail_open"] = str(hero_open_path.relative_to(ROOT))
                    letter_box = page.locator(".moving-letter").bounding_box()
                    sheet_box = page.locator(".letter-sheet").bounding_box()
                    pocket_box = page.locator(".letter-pocket").bounding_box()
                    speech_box = page.locator(".speech-cloud").bounding_box()
                    self.assertLess(sheet_box["y"], letter_box["y"], profile_label)
                    self.assert_inside(sheet_box, page.locator(".post-office").bounding_box(), f"{profile_label}: opened letter sheet")
                    self.assert_inside(pocket_box, letter_box, f"{profile_label}: envelope front pocket")
                    if viewport["width"] <= 380:
                        self.assertLessEqual(
                            speech_box["y"] + speech_box["height"],
                            sheet_box["y"] + 2,
                            f"{profile_label}: quote card obscures the opened letter",
                        )
                    self.assertEqual(page.locator(".letter-seal").count(), 0)
                    self.assertEqual(page.locator(".letter-heart").evaluate("element => getComputedStyle(element).opacity"), "0")

                    motion = page.locator("#motionToggle")
                    self.assertTrue(motion.is_visible(), profile_label)
                    self.assertEqual(motion.locator(".button-label").inner_text(), "Animációk leállítása")
                    motion.click()
                    self.assertEqual(motion.get_attribute("aria-pressed"), "true")
                    self.assertEqual(motion.locator(".button-label").inner_text(), "Animációk indítása")

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

                    encryption_label_margins = []
                    for mode in ("https", "providerRest", "userRest", "e2ee"):
                        page.locator(f'encryption-layers [data-encryption="{mode}"]').click()
                        diagram = page.locator("encryption-layers .crypto-diagram").bounding_box()
                        labels = page.locator(
                            "encryption-layers .crypto-packet:visible, "
                            "encryption-layers .crypto-key-chip:visible, "
                            "encryption-layers .crypto-access-state:visible"
                        )
                        for index, label in enumerate(labels.all()):
                            label_box = label.bounding_box()
                            self.assert_inside(
                                label_box,
                                diagram,
                                f"{profile_label}: {mode} diagram label {index + 1}",
                            )
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
                                f"{profile_label}: {mode} graphic {index + 1} lacks left shadow clearance",
                            )
                            self.assertLessEqual(
                                graphic_box["x"] + graphic_box["width"],
                                diagram["x"] + diagram["width"] - 6,
                                f"{profile_label}: {mode} graphic {index + 1} lacks right shadow clearance",
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
                            self.assertTrue(separated, f"{profile_label}: {mode} access-state chips overlap")
                        if mode == "userRest":
                            encryption_path = artifact_dir / "06-encryption-user-key.jpg"
                            page.locator("encryption-layers .encryption-shell").screenshot(
                                path=str(encryption_path), type="jpeg", quality=58
                            )
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

                    page.locator("vote-explorer").scroll_into_view_if_needed()
                    page.wait_for_timeout(50)
                    vote_picker = page.locator("vote-explorer .vote-picker")
                    active_vote = vote_picker.locator('[aria-selected="true"]')
                    self.assert_inside(active_vote.bounding_box(), vote_picker.bounding_box(), f"{profile_label}: active vote tab")
                    initial_member_count = page.locator("vote-explorer .member-grid article").count()
                    expected_member_limit = 10 if viewport["width"] <= 600 else 48
                    self.assertLessEqual(initial_member_count, expected_member_limit, profile_label)
                    vote_path = artifact_dir / "10-vote-explorer.jpg"
                    page.locator("vote-explorer .vote-explorer-shell").screenshot(path=str(vote_path), type="jpeg", quality=58)
                    screenshot_paths["vote_explorer"] = str(vote_path.relative_to(ROOT))

                    safeguard_shell = page.locator("safeguard-builder .safeguard-shell")
                    safeguard_shell_box = safeguard_shell.bounding_box()
                    self.assert_inside(page.locator("safeguard-builder .safeguard-visual").bounding_box(), safeguard_shell_box, f"{profile_label}: safeguard visual")
                    self.assert_inside(page.locator("safeguard-builder .safeguard-options").bounding_box(), safeguard_shell_box, f"{profile_label}: safeguard options")
                    for index, option in enumerate(page.locator("safeguard-builder [data-safeguard]").all()):
                        self.assert_inside(option.bounding_box(), safeguard_shell_box, f"{profile_label}: safeguard option {index + 1}")
                    safeguard_path = artifact_dir / "11-safeguards.jpg"
                    safeguard_shell.screenshot(path=str(safeguard_path), type="jpeg", quality=58)
                    screenshot_paths["safeguards"] = str(safeguard_path.relative_to(ROOT))

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
                        "profile_index": profile_index,
                        "name": name,
                        "viewport": viewport,
                        "screenshots": screenshot_paths,
                        "analysis": {
                            "horizontal_overflow_px": overflow,
                            "minimum_action_copy_to_button_gap_px": min(action_gaps),
                            "recipient_key_clearance_px": round(key_clearance, 2),
                            "minimum_encryption_label_edge_margin_px": min(encryption_label_margins),
                            "minimum_readable_helper_font_px": min(readable_sizes),
                            "minimum_diagram_label_font_px": min(diagram_sizes),
                            "visible_help_directory_cards": visible_connection_cards,
                            "initial_vote_member_cards": initial_member_count,
                            "opened_letter_sheet_rise_px": round(letter_box["y"] - sheet_box["y"], 2),
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
