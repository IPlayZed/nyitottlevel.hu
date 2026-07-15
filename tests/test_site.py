import functools
import http.server
import pathlib
import re
import tarfile
import threading
import unittest

from playwright.sync_api import sync_playwright


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHROMIUM = "/usr/bin/chromium-browser"


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
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

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on(
            "console",
            lambda message: self.errors.append(message.text)
            if message.type == "error"
            else None,
        )
        self.page.goto(self.base_url, wait_until="networkidle")

    def tearDown(self):
        self.assertEqual(self.errors, [], f"Böngészőhiba: {self.errors}")
        self.context.close()

    def test_page_loads_and_has_no_horizontal_overflow(self):
        self.assertIn("Felbontanád mindenki levelét", self.page.title())
        self.assertTrue(self.page.get_by_role("heading", name="Felbontanád mindenki levelét", exact=False).is_visible())
        self.assertEqual(self.page.locator("mail-story .mail-stage").count(), 1)
        self.assertGreaterEqual(float(self.page.evaluate("parseFloat(getComputedStyle(document.body).fontSize)")), 18)
        self.assertGreaterEqual(float(self.page.evaluate("parseFloat(getComputedStyle(document.querySelector('.risk-grid p')).fontSize)")), 15)
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        self.assertEqual(self.page.locator("main > section").count(), 13)
        self.assertEqual(self.page.locator("[data-language-toggle]").count(), 0)
        self.assertEqual(self.page.locator('script[src^="locales/"]').count(), 0)
        self.assertEqual(self.page.locator('script[src="full-i18n.js"]').count(), 0)
        self.assertIn("aggódó állampolgár", self.page.locator("footer").inner_text().lower())
        self.assertIn("nem támogat egyetlen politikai pártot sem", self.page.locator("footer").inner_text().lower())

    def test_header_subsections_have_real_targets_and_mobile_groups(self):
        self.assertEqual(self.page.locator(".desktop-nav .nav-group").count(), 4)
        self.assertEqual(self.page.locator(".desktop-nav .nav-submenu a").count(), 12)
        self.assertEqual(self.page.locator('.desktop-nav > a.nav-direct[href="#gyakori-tevhitek"]').count(), 1)
        self.assertEqual(self.page.locator("#mobileNav .mobile-nav__group").count(), 4)
        self.assertEqual(self.page.locator('#mobileNav > a.mobile-nav__shortcut[href="#gyakori-tevhitek"]').count(), 1)
        missing_targets = self.page.evaluate(
            """() => [...document.querySelectorAll('.desktop-nav a[href^="#"], #mobileNav a[href^="#"]')]
              .map(link => link.getAttribute('href'))
              .filter((href, index, all) => all.indexOf(href) === index)
              .filter(href => !document.querySelector(href))"""
        )
        self.assertEqual(missing_targets, [])

    def test_common_misconceptions_are_linkable_balanced_and_sourced(self):
        section = self.page.locator("#gyakori-tevhitek")
        self.assertTrue(section.is_visible())
        self.assertEqual(section.locator(".misconception-card").count(), 4)

        expected_ids = (
            "nincs-mit-rejtegetnem",
            "csak-bunozoket-erint",
            "minden-uzenetet-olvasnak",
            "titkositas-betiltasa",
        )
        for card_id in expected_ids:
            with self.subTest(card=card_id):
                card = section.locator(f"#{card_id}")
                self.assertTrue(card.is_visible())
                self.assertEqual(card.locator(".section-anchor").get_attribute("href"), f"#{card_id}")
                self.assertIn("Röviden:", card.inner_text())

        copy = section.inner_text().lower()
        self.assertIn("a magánszféra nem a bűnösség jele", copy)
        self.assertIn("meghatározott szolgáltatásra és kockázattípusra", copy)
        self.assertIn("nem minden szolgáltató fér hozzá minden üzenethez", copy)
        self.assertIn("a jog korlátozhatja a titkosítás használatát", copy)

        external_sources = section.locator('.misconception-sources a[target="_blank"]')
        self.assertEqual(external_sources.count(), 6)
        for link in external_sources.all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))
            self.assertIn("noreferrer", link.get_attribute("rel") or "")
        self.assertEqual(section.locator('.misconception-sources a[href="#posta"]').count(), 1)

        self.page.set_viewport_size({"width": 320, "height": 720})
        self.page.goto(f"{self.base_url}/#gyakori-tevhitek", wait_until="networkidle")
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        self.assertEqual(section.locator(".misconception-card").count(), 4)

        self.page.set_viewport_size({"width": 834, "height": 900})
        self.page.goto(f"{self.base_url}/#gyakori-tevhitek", wait_until="networkidle")
        clipped_heading_children = self.page.evaluate(
            """() => {
              const heading = document.querySelector('.misconceptions-heading');
              const bounds = heading.getBoundingClientRect();
              return [...heading.children].map(child => {
                const rect = child.getBoundingClientRect();
                return {left: rect.left, right: rect.right};
              }).filter(rect => rect.left < bounds.left - 1 || rect.right > bounds.right + 1);
            }"""
        )
        self.assertEqual(clipped_heading_children, [])
        self.assertLessEqual(section.evaluate("element => element.scrollWidth - element.clientWidth"), 1)

    def test_public_feedback_and_license_links_are_explicit(self):
        feedback_url = "https://github.com/IPlayZed/nyitottlevel.hu/issues/new?template=feedback_hu.yml"
        feedback_links = self.page.locator(f'a[href="{feedback_url}"]')
        self.assertEqual(feedback_links.count(), 2)
        for link in feedback_links.all():
            self.assertEqual(link.get_attribute("target"), "_blank")
            self.assertIn("noreferrer", link.get_attribute("rel"))
        self.assertIn("AGPL-3.0-or-later", self.page.locator("footer").inner_text())
        self.assertEqual(self.page.locator('footer a[href="LICENSE"]').count(), 1)
        self.assertTrue((ROOT / "LICENSE").is_file())
        issue_template = ROOT / ".github" / "ISSUE_TEMPLATE" / "feedback_hu.yml"
        self.assertTrue(issue_template.is_file())
        self.assertIn("Visszajelzés az oldalról", issue_template.read_text(encoding="utf-8"))

    def test_static_security_policy_and_external_link_invariants(self):
        csp = self.page.locator('meta[http-equiv="Content-Security-Policy"]').get_attribute("content")
        for directive in ("default-src 'self'", "object-src 'none'", "base-uri 'none'", "form-action 'none'"):
            self.assertIn(directive, csp)
        self.assertNotIn("upgrade-insecure-requests", csp)
        self.assertEqual(self.page.locator('meta[name="referrer"]').get_attribute("content"), "no-referrer")

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Enforce HTTPS", readme)
        self.assertIn("GitHub Pages does not provide repository-controlled custom response headers", readme)

        for link in self.page.locator('a[target="_blank"]').all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))
            self.assertIn("noreferrer", link.get_attribute("rel") or "")
        self.assertEqual(self.page.locator('[onclick], [onerror], [onload], a[href^="javascript:"]').count(), 0)
        self.assertEqual(self.page.locator('script[src^="http"], link[rel="stylesheet"][href^="http"], img[src^="http"], iframe').count(), 0)

    def test_committed_data_templates_escape_text_and_reject_unsafe_urls(self):
        self.page.evaluate(
            """() => {
              const payload = '<img src=x onerror=alert(1)>';
              window.CHAT_CONTROL_VOTES = [{
                key: 'malicious', short_date: payload, title: payload, body: payload,
                question: payload, meaning: payload, result_label: payload,
                totals: { FOR: 1, AGAINST: 0, ABSTENTION: 0, DID_NOT_VOTE: null },
                position_labels: { FOR: payload, AGAINST: 'Nem', ABSTENTION: 'Tartózkodott', DID_NOT_VOTE: 'Nem szavazott' },
                members: [{ name: payload, country: '<b>HU</b>', group: payload, position: 'FOR' }],
                group_stats: [{ group: payload, label: payload, stats: { FOR: 1 } }],
                official_source: 'javascript:alert(1)', explore_source: 'http://unsafe.example/'
              }];
              const explorer = document.querySelector('vote-explorer');
              explorer.voteKey = 'malicious';
              explorer.view = 'members';
              explorer.render();
            }"""
        )
        explorer = self.page.locator("vote-explorer")
        self.assertEqual(explorer.locator("img, script, [onerror], [onclick]").count(), 0)
        self.assertIn("<img src=x onerror=alert(1)>", explorer.inner_text())
        for link in explorer.locator(".vote-sources a").all():
            self.assertEqual(link.get_attribute("href"), "#")

        self.page.evaluate(
            """() => {
              const payload = '<img src=x onerror=alert(2)>';
              const quiz = document.querySelector('myth-quiz');
              quiz.questions = [{ id: 'malicious', category: 'test', categoryLabel: payload, statement: payload, detail: payload, answer: true }];
              quiz.index = 0;
              quiz.score = 0;
              quiz.answered = false;
              quiz.render();
            }"""
        )
        quiz = self.page.locator("myth-quiz")
        self.assertEqual(quiz.locator("img, script, [onerror], [onclick]").count(), 0)
        self.assertIn("<img src=x onerror=alert(2)>", quiz.inner_text())
        quiz.locator('[data-answer="true"]').click()
        self.assertEqual(quiz.locator("img, script, [onerror], [onclick]").count(), 0)
        self.assertIn("<img src=x onerror=alert(2)>", quiz.locator(".quiz-feedback").inner_text())

    def test_mail_story_and_version_switcher(self):
        self.assertEqual(self.page.locator(".moving-letter .letter-flap").count(), 1)
        self.assertEqual(self.page.locator(".moving-letter .letter-pocket").count(), 1)
        self.assertEqual(self.page.locator(".moving-letter .letter-seal").count(), 0)
        self.assertEqual(self.page.locator("mail-story .mail-opening-label").count(), 1)
        for step in range(4):
            self.page.locator(f'mail-story [data-step="{step}"]').click()
            finite_animations = self.page.locator("mail-story .mail-illustration").evaluate("""illustration => {
              const finite = [];
              const nodes = [illustration, ...illustration.querySelectorAll('*')];
              for (const node of nodes) {
                for (const pseudo of [null, '::before', '::after']) {
                  const style = getComputedStyle(node, pseudo);
                  const names = style.animationName.split(',').map(value => value.trim());
                  const counts = style.animationIterationCount.split(',').map(value => value.trim());
                  names.forEach((name, index) => {
                    if (name !== 'none' && counts[index % counts.length] !== 'infinite') {
                      finite.push(`${node.className || node.tagName}${pseudo || ''}: ${name}`);
                    }
                  });
                }
              }
              return finite;
            }""")
            self.assertEqual(finite_animations, [], f"Mail-story step {step + 1} has finite animations")
        self.page.locator('mail-story [data-step="0"]').click()
        self.assertEqual(self.page.locator("mail-story .mail-envelope-flap").count(), 1)
        self.assertEqual(self.page.locator("mail-story .mail-envelope-pocket").count(), 1)
        self.assertEqual(self.page.locator("mail-story .mail-note > i").count(), 2)
        self.page.locator("mail-story [data-mail-next]").click()
        self.assertIn("olvashatatlan, titkosított adat", self.page.locator("mail-story h3").inner_text())
        mail_story = self.page.locator("mail-story")
        self.assertEqual(mail_story.locator(".mail-object.is-e2ee").count(), 1)
        self.assertIn("7F A9", mail_story.locator(".mail-note-cipher").inner_text())
        self.assertEqual(mail_story.locator(".mail-e2ee-no-key").count(), 1)
        self.assertEqual(mail_story.locator(".mail-e2ee-key").count(), 1)
        self.assertEqual(mail_story.locator(".mail-e2ee-key-traveller").count(), 0)
        self.assertIn("a kulcs nem kerül a szolgáltatóhoz", mail_story.locator(".mail-e2ee-key").inner_text().lower())
        comparison = mail_story.locator(".mail-key-comparison").inner_text().lower()
        self.assertIn("kulcs nélkül", comparison)
        self.assertIn("a címzett digitális kulcsával", comparison)
        explanation = mail_story.locator(".mail-copy").inner_text().lower()
        self.assertIn("kulcs nélkül", explanation)
        self.assertIn("a címzett készüléke tudja visszaállítani", explanation)
        self.page.locator('mail-story [data-step="2"]').click()
        self.assertEqual(mail_story.locator(".mail-inspection-booth").count(), 1)
        self.assertEqual(mail_story.locator(".mail-object.is-inspected").count(), 1)
        self.assertIn("ha a szolgáltató az eredeti üzenetet vizsgálja", mail_story.locator("h3").inner_text().lower())
        self.assertIn("a belső boríték itt felnyílik", mail_story.locator(".mail-copy").inner_text().lower())
        self.page.locator('mail-story [data-step="3"]').click()
        self.assertEqual(mail_story.locator(".mail-before-device").count(), 1)
        self.assertEqual(mail_story.locator(".mail-object.is-before-check").count(), 1)
        self.assertIn("lezárás előtt", mail_story.locator("h3").inner_text().lower())
        self.assertIn("csak ezután zárja le a készülék", mail_story.locator(".mail-copy").inner_text().lower())
        self.page.get_by_role("tab", name="2.0 · tervezett").click()
        self.assertEqual(self.page.locator("version-switcher h3").inner_text(), "Chat Control 2.0")
        self.assertIn("nincs végleges megállapodás", self.page.locator("version-switcher").inner_text().lower())
        self.page.get_by_role("tab", name="2.0 · tervezett").press("ArrowLeft")
        self.assertEqual(self.page.get_by_role("tab", name="1.0 · ideiglenes").get_attribute("aria-selected"), "true")

    def test_interactive_sections_use_wide_desktop_rail(self):
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        for selector in (
            "mail-story .interactive-card",
            "version-switcher .version-shell",
            "detection-lab .lab-shell",
            "privacy-room .room-shell",
            ".vote-board",
            "encryption-layers .encryption-shell",
        ):
            with self.subTest(selector=selector):
                width = self.page.locator(selector).bounding_box()["width"]
                self.assertGreaterEqual(width, 1300, f"{selector} remained too narrow: {width}px")

    def test_institutions_lab_and_privacy_cases(self):
        self.page.get_by_role("button", name="Mit változtatott?").click()
        parliament = self.page.locator(".institution-card--parliament")
        self.assertIn("is-flipped", parliament.get_attribute("class"))
        self.assertIn("Célzottabb végzések", parliament.locator(".institution-card__back").inner_text())
        self.page.get_by_role("tab", name="Beszélgetés értelmezése").click()
        self.assertIn("teljes beszélgetés", self.page.locator("detection-lab .lab-copy h3").inner_text())
        slider = self.page.locator("#falseRate")
        self.page.locator("#falseRate").fill("1")
        self.assertEqual(slider.input_value(), "1")
        self.assertEqual(self.page.locator("detection-lab [data-fp]").inner_text(), "100")
        self.assertEqual(self.page.locator("detection-lab [data-fn]").inner_text(), "1")
        self.assertEqual(self.page.locator("detection-lab [data-tn]").inner_text().replace("\xa0", "").replace(" ", ""), "9890")
        self.page.locator("#sensitivity").fill("70")
        self.assertEqual(self.page.locator("detection-lab [data-tp]").inner_text(), "7")
        self.assertEqual(self.page.locator("detection-lab [data-fn]").inner_text(), "3")
        self.assertEqual(self.page.locator("detection-lab [data-fp]").inner_text(), "100")
        for slider_id in ("#prevalence", "#sensitivity", "#falseRate"):
            self.assertEqual(self.page.locator(slider_id).get_attribute("min"), "0")
            self.assertEqual(self.page.locator(slider_id).get_attribute("max"), "100")
        self.page.locator("#prevalence").fill("1")
        self.assertEqual(self.page.locator("detection-lab [data-tp]").inner_text(), "70")
        self.assertEqual(self.page.locator("detection-lab [data-fn]").inner_text(), "30")
        self.assertEqual(self.page.locator("detection-lab [data-fp]").inner_text(), "99")
        self.assertEqual(self.page.locator("detection-lab [data-tn]").inner_text().replace("\xa0", "").replace(" ", ""), "9801")
        self.assertEqual(self.page.locator("detection-lab [data-specificity]").inner_text(), "99,0%")
        self.assertEqual(self.page.locator("detection-lab [data-ppv]").inner_text(), "41,4%")
        self.page.locator("#prevalence").fill("100")
        self.assertEqual(self.page.locator("detection-lab [data-fp]").inner_text(), "0")
        self.assertEqual(self.page.locator("detection-lab [data-tn]").inner_text(), "0")
        self.assertEqual(self.page.locator("detection-lab [data-specificity]").inner_text(), "Nem értelmezhető")
        self.assertEqual(self.page.locator(".population-canvas").count(), 1)
        self.page.get_by_role("tab", name="Újságíró", exact=True).click()
        self.assertIn("visszaélés bizonyítékát", self.page.locator("privacy-room h3").inner_text())
        self.assertIn("person-figure--journalist", self.page.locator("privacy-room .person-figure").get_attribute("class"))
        self.assertEqual(self.page.locator("privacy-room .person-gear").inner_text(), "PRESS")

    def test_targeted_and_mass_surveillance_are_visually_distinct(self):
        explainer = self.page.locator("surveillance-contrast")
        self.assertEqual(explainer.get_by_role("tab").count(), 2)
        self.assertEqual(explainer.locator(".surveillance-person").count(), 30)
        self.assertEqual(explainer.locator(".surveillance-person.is-target").count(), 1)
        self.assertIn("nem vizsgálja át automatikusan mind a harminc", explainer.inner_text().lower())
        explainer.get_by_role("tab", name="Általános átvizsgálás").click()
        self.assertEqual(explainer.locator(".surveillance-person.is-flagged").count(), 3)
        copy = explainer.inner_text().lower()
        self.assertIn("nem kell embernek kézzel elolvasnia", copy)
        self.assertIn("metaadat", copy)
        self.assertIn("mind a 30 ember adatait", copy)
        for link in explainer.locator(".surveillance-sources a").all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))

    def test_connection_directory_separates_help_research_and_community(self):
        directory = self.page.locator("#kapcsolodas")
        cards = directory.locator("[data-connection-card]")
        self.assertEqual(cards.count(), 16)
        self.assertEqual(directory.locator("[data-connection-filter]").count(), 4)
        directory.get_by_role("button", name="Segítség és panasz").click()
        visible_help = directory.locator("[data-connection-card]:visible")
        self.assertEqual(visible_help.count(), 6)
        self.assertTrue(any("NAIH" in text for text in visible_help.all_inner_texts()))
        self.assertEqual(directory.locator("[data-connection-count]").inner_text(), "6")
        directory.get_by_role("button", name="Közösség és részvétel").click()
        visible_community = directory.locator("[data-connection-card]:visible")
        self.assertGreaterEqual(visible_community.count(), 7)
        self.assertTrue(any("H.A.C.K." in text for text in visible_community.all_inner_texts()))
        for link in cards.locator("a").all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))

    def test_connection_route_uses_short_non_overlapping_mobile_separators(self):
        self.page.set_viewport_size({"width": 539, "height": 980})
        self.page.goto(f"{self.base_url}/#kapcsolodas", wait_until="networkidle")
        route = self.page.locator("#kapcsolodas .connection-route")
        route.scroll_into_view_if_needed()
        self.page.wait_for_timeout(100)
        layout = route.evaluate(
            """element => [...element.children].map(child => {
              const rect = child.getBoundingClientRect();
              const own = getComputedStyle(child);
              const marker = getComputedStyle(child, '::before');
              return {
                tag: child.tagName,
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                background: own.backgroundColor,
                transform: own.transform,
                markerWidth: parseFloat(marker.width),
                markerHeight: parseFloat(marker.height),
                markerContent: marker.content,
              };
            })"""
        )
        cards = [item for item in layout if item["tag"] == "ARTICLE"]
        separators = [item for item in layout if item["tag"] == "I"]
        self.assertEqual(len(cards), 3)
        self.assertEqual(len(separators), 2)

        for index, separator_box in enumerate(separators):
            previous_card = cards[index]
            next_card = cards[index + 1]
            self.assertLessEqual(separator_box["height"], 44, f"separator {index + 1} is too tall")
            self.assertGreaterEqual(separator_box["y"], previous_card["y"] + previous_card["height"] - 1)
            self.assertLessEqual(separator_box["y"] + separator_box["height"], next_card["y"] + 1)
            self.assertIn(separator_box["background"], ("rgba(0, 0, 0, 0)", "transparent"))
            self.assertEqual(separator_box["transform"], "none")
            self.assertLessEqual(separator_box["markerWidth"], 36)
            self.assertLessEqual(separator_box["markerHeight"], 36)
            self.assertNotEqual(separator_box["markerContent"], "none")

        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        artifact_dir = ROOT / "test-artifacts" / "regressions"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        route.screenshot(path=str(artifact_dir / "539x980-connection-route.png"), animations="disabled")

    def test_detection_math_invariants_and_zero_alert_state(self):
        cases = (
            (1, 0, 0, 0),
            (1000, 0.1, 90, 0.5),
            (10000, 1, 70, 1),
            (12345, 50, 50, 50),
            (100000000, 100, 100, 100),
        )
        for total, prevalence, sensitivity, false_rate in cases:
            with self.subTest(total=total, prevalence=prevalence, sensitivity=sensitivity, false_rate=false_rate):
                self.page.locator("#messageTotal").fill(str(total))
                self.page.locator("#prevalence").fill(str(prevalence))
                self.page.locator("#sensitivity").fill(str(sensitivity))
                self.page.locator("#falseRate").fill(str(false_rate))
                counts = [
                    int(self.page.locator(f"detection-lab [{field}]").inner_text().replace("\xa0", "").replace(" ", ""))
                    for field in ("data-tp", "data-fn", "data-fp", "data-tn")
                ]
                positives = int(total * prevalence / 100 + 0.5)
                self.assertEqual(sum(counts), total)
                self.assertEqual(counts[0] + counts[1], positives)
                self.assertEqual(counts[2] + counts[3], total - positives)

        self.page.locator("#messageTotal").fill("10000")
        self.page.locator("#prevalence").fill("0")
        self.page.locator("#sensitivity").fill("0")
        self.page.locator("#falseRate").fill("0")
        self.assertEqual(self.page.locator("detection-lab [data-ppv]").inner_text(), "Nem értelmezhető")
        self.assertIn("Nincs riasztás", self.page.locator("detection-lab [data-rate-summary]").inner_text())
        self.assertIn("Nincs riasztás", self.page.locator("detection-lab [data-alert-caption]").inner_text())

        self.page.locator("#prevalence").fill("0.1")
        self.page.locator("#sensitivity").fill("90")
        self.page.locator("#falseRate").fill("0.5")
        population_caption = self.page.locator("[data-population-caption]").inner_text().replace("\xa0", " ")
        self.assertIn("10 000 üzenet · egy éles pont egy üzenet", population_caption)
        population_canvas = self.page.locator(".population-canvas")
        self.assertTrue(population_canvas.is_visible())
        self.assertTrue(self.page.locator("[data-population-composition]").is_hidden())
        self.assertGreaterEqual(int(population_canvas.get_attribute("width")), int(population_canvas.bounding_box()["width"]))
        alert_canvas = self.page.locator(".alert-canvas")
        self.assertGreaterEqual(int(alert_canvas.get_attribute("width")), int(alert_canvas.bounding_box()["width"]))
        rare_cards = self.page.locator("detection-lab .rare-count")
        self.assertEqual(rare_cards.count(), 4)
        self.assertEqual(rare_cards.nth(0).locator(".rare-dot").count(), 9)
        self.assertEqual(rare_cards.nth(1).locator(".rare-dot").count(), 1)
        self.assertEqual(rare_cards.nth(2).locator(".rare-dot").count(), 20)
        self.assertEqual(rare_cards.nth(2).locator(".rare-more").count(), 1)
        self.assertEqual(rare_cards.nth(0).get_attribute("aria-label"), "Valódi találat: 9")

        self.page.locator("#messageTotal").fill("1000000")
        population_caption = self.page.locator("[data-population-caption]").inner_text().replace("\xa0", " ")
        self.assertIn("1 000 000 üzenet", population_caption)
        self.assertIn("pontos darabszámok és arányok, pontfelhő helyett", population_caption)
        self.assertTrue(self.page.locator("[data-population-composition]").is_visible())
        self.assertTrue(self.page.locator(".population-canvas").is_hidden())
        self.assertEqual(self.page.locator(".composition-card").count(), 4)
        composition_counts = [
            int(text.replace("\xa0", "").replace(" ", ""))
            for text in self.page.locator(".composition-card strong").all_inner_texts()
        ]
        self.assertEqual(sum(composition_counts), 1000000)
        self.assertIn("egészre kerekített darabszámok alapján", self.page.locator("[data-specificity] + small").inner_text())

        lab = self.page.locator("detection-lab")
        lab.evaluate("element => element.drawPopulationComposition({tp: 1, fn: 0, fp: 0, tn: 99999999, total: 100000000})")
        self.assertEqual(self.page.locator(".composition-card--tp b").inner_text(), "<0,001%")
        self.page.locator("#messageTotal").fill("1.5")
        self.assertEqual(self.page.locator("#messageTotal").input_value(), "2")
        self.page.locator("#messageTotal").fill("0")
        self.assertEqual(self.page.locator("#messageTotal").input_value(), "1")
        self.page.locator("#messageTotal").fill("100000001")
        self.assertEqual(self.page.locator("#messageTotal").input_value(), "100000000")
        self.assertEqual(self.page.locator("#messageTotal").get_attribute("min"), "1")
        self.assertEqual(self.page.locator("#messageTotal").get_attribute("max"), "100000000")

    def test_report_source_count_is_precise_without_claiming_every_source_is_primary(self):
        report_path = ROOT / "chat-control-report.md"
        report_bytes = report_path.read_bytes()
        self.assertTrue(report_bytes.startswith(b"\xef\xbb\xbf"), "The directly linked Markdown needs a UTF-8 BOM for browsers that ignore text-file charset metadata")
        report = report_path.read_text(encoding="utf-8-sig")
        urls = set(re.findall(r"https?://[^\s)>]+", report))
        words = len(report.split())
        self.assertEqual(len(urls), 61)
        self.assertEqual(words, 13240)
        banner = self.page.locator(".action-banner h3").inner_text()
        self.assertIn("13 240 szavas", banner)
        self.assertIn("61 egyedi hivatkozott forrással", banner)
        self.assertNotIn("61 elsődleges", banner)
        self.page.route("**/favicon.ico", lambda route: route.fulfill(status=204, body=""))
        self.page.goto(f"{self.base_url}/chat-control-report.md", wait_until="networkidle")
        rendered_report = self.page.locator("body").inner_text()
        self.assertIn("A „Chat Control” az Európai Unióban", rendered_report)
        self.assertNotIn("â€", rendered_report)

    def test_abuse_paths_and_documented_cases(self):
        self.assertEqual(self.page.locator("abuse-simulator [data-abuse]").count(), 6)
        for button in self.page.locator("abuse-simulator [data-abuse]").all():
            icon = button.locator("span")
            icon_box = icon.bounding_box()
            self.assertGreaterEqual(icon_box["width"], 36)
            self.assertGreaterEqual(float(icon.evaluate("node => parseFloat(getComputedStyle(node).fontSize)")), 24)
            self.assertNotEqual(
                icon.evaluate("node => getComputedStyle(node).backgroundColor"),
                button.evaluate("node => getComputedStyle(node).backgroundColor"),
            )
        self.page.get_by_role("tab", name="Forrásvédelem").click()
        self.assertIn("öncenzúrát", self.page.locator("abuse-simulator .abuse-path").inner_text())
        self.assertEqual(self.page.locator("abuse-history .history-case").count(), 9)
        self.page.get_by_role("button", name="Vállalati hozzáférés").click()
        self.assertEqual(self.page.locator("abuse-history .history-case").count(), 2)
        self.assertIn("Twitter", self.page.locator("abuse-history").inner_text())

    def test_vote_quiz_dialog_and_motion_control(self):
        self.page.get_by_role("button", name="Mutasd a 314 szavazatot").click()
        self.assertTrue(self.page.locator(".vote-explainer").is_visible())
        self.assertIn("46 hiányzott", self.page.locator("[data-run-vote]").inner_text())
        statement = self.page.locator("myth-quiz .quiz-card h3").inner_text()
        answer = self.page.evaluate(
            "statement => window.CHAT_CONTROL_QUIZ.find(question => question.statement === statement).answer",
            statement,
        )
        self.page.locator(f"myth-quiz [data-answer='{str(answer).lower()}']").click()
        self.assertIn("Pontosan", self.page.locator("myth-quiz .quiz-feedback").inner_text())
        self.page.get_by_role("button", name="Mi a helyzet most?").click()
        self.assertTrue(self.page.locator("#statusDialog").is_visible())
        self.page.locator("#statusDialog .dialog-close").click()
        self.page.locator("#motionToggle").click()
        self.assertEqual(self.page.locator("html").get_attribute("data-reduce-motion"), "true")

    def test_vote_explorer_and_balanced_quiz_set(self):
        self.assertEqual(self.page.locator(".vote-chronology li").count(), 5)
        vote_order = self.page.evaluate(
            """() => [...document.querySelector('#szavazas').children].map(element => ['vote-explorer','vote-simulator'].includes(element.tagName.toLowerCase()) ? element.tagName.toLowerCase() : [...element.classList][0]).filter(Boolean)"""
        )
        self.assertLess(vote_order.index("vote-chronology"), vote_order.index("vote-explorer"))
        self.assertLess(vote_order.index("vote-explorer"), vote_order.index("vote-threshold-intro"))
        self.assertLess(vote_order.index("vote-threshold-intro"), vote_order.index("vote-simulator"))
        self.assertEqual(self.page.locator("vote-explorer [data-vote-key]").count(), 5)
        self.page.locator('vote-explorer [data-vote-key="2023-libe-position"]').click()
        self.assertEqual(self.page.locator("vote-explorer .vote-total-cards > div").last.locator("b").inner_text(), "—")
        self.page.locator("vote-explorer [data-hungarian-filter]").click()
        self.assertIn("Katalin Cseh", self.page.locator("vote-explorer .member-grid").inner_text())
        self.page.locator('vote-explorer [data-vote-key="2026-july-rejection"]').click()
        self.assertTrue(self.page.evaluate("() => window.CHAT_CONTROL_VOTES.every(vote => vote.members.every(member => typeof member.name === 'string' && member.name.trim().length > 0))"))
        for card in self.page.locator("vote-explorer .member-grid article").all():
            label_box = card.locator(".member-position").bounding_box()
            name_box = card.locator("h5").bounding_box()
            self.assertGreaterEqual(name_box["y"], label_box["y"] + label_box["height"] - 1)
            self.assertTrue(card.locator("h5").inner_text().strip())
        self.page.locator("vote-explorer [data-hungarian-filter]").click()
        members = self.page.locator("vote-explorer .member-grid article")
        self.assertGreater(members.count(), 0)
        for card in members.all():
            self.assertIn("HU", card.inner_text())
        quiz_shape = self.page.evaluate(
            """() => {
              const questions = document.querySelector('myth-quiz').questions;
              let streak = 1;
              let longest = 1;
              for (let i = 1; i < questions.length; i += 1) {
                streak = questions[i].answer === questions[i - 1].answer ? streak + 1 : 1;
                longest = Math.max(longest, streak);
              }
              return {
                total: questions.length,
                trueCount: questions.filter(question => question.answer).length,
                categories: new Set(questions.map(question => question.category)).size,
                longest,
                bank: window.CHAT_CONTROL_QUIZ.length,
              };
            }"""
        )
        self.assertEqual(
            {key: quiz_shape[key] for key in ("total", "trueCount", "categories", "bank")},
            {"total": 10, "trueCount": 5, "categories": 10, "bank": 100},
        )
        self.assertLessEqual(quiz_shape["longest"], 2)
        first_ids = self.page.evaluate("() => document.querySelector('myth-quiz').questions.map(question => question.id)")
        for _ in range(10):
            current_answer = self.page.evaluate(
                "() => { const quiz = document.querySelector('myth-quiz'); return quiz.questions[quiz.index].answer; }"
            )
            self.page.locator(f"myth-quiz [data-answer='{str(current_answer).lower()}']").click()
            self.page.locator("myth-quiz [data-next-question]").click()
        self.assertTrue(self.page.get_by_role("button", name="10 új kérdés").is_visible())
        self.page.get_by_role("button", name="10 új kérdés").click()
        second_ids = self.page.evaluate("() => document.querySelector('myth-quiz').questions.map(question => question.id)")
        self.assertEqual(len(set(first_ids).intersection(second_ids)), 0)

    def test_mobile_navigation_and_layout(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        motion = self.page.locator("#motionToggle")
        self.assertTrue(motion.is_visible())
        self.assertEqual(motion.locator(".button-label").inner_text(), "Animációk leállítása")
        motion.click()
        self.assertEqual(motion.locator(".button-label").inner_text(), "Animációk indítása")
        self.assertEqual(motion.get_attribute("aria-pressed"), "true")
        self.page.locator("#menuButton").click()
        self.assertEqual(self.page.locator("#menuButton").get_attribute("aria-expanded"), "true")
        self.assertTrue(self.page.locator("#mobileNav").is_visible())
        self.page.locator("#mobileNav a").first.click()
        self.assertEqual(self.page.locator("#menuButton").get_attribute("aria-expanded"), "false")
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        self.assertGreaterEqual(self.page.locator("#menuButton").bounding_box()["width"], 44)

    def test_mobile_vote_list_starts_with_six_names_and_can_expand(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.reload(wait_until="networkidle")
        self.assertEqual(self.page.locator("vote-explorer .member-grid article").count(), 6)
        more = self.page.locator("vote-explorer [data-vote-more]")
        self.assertIn("További 6 képviselő", more.inner_text())
        more.click()
        self.assertEqual(self.page.locator("vote-explorer .member-grid article").count(), 12)

    def test_action_dialog_and_source_links(self):
        self.page.get_by_role("button", name="Levélminta megnyitása").click()
        self.assertTrue(self.page.locator("#letterDialog").is_visible())
        self.assertIn("végpontok közötti titkosítás", self.page.locator("#letterTemplate").input_value())
        self.page.keyboard.press("Escape")
        self.assertFalse(self.page.locator("#letterDialog").is_visible())
        self.assertEqual(self.page.locator(".source-links a").count(), 6)
        self.assertIn("/HU/", self.page.locator('.source-links a[href*="eur-lex"]').first.get_attribute("href"))
        for link in self.page.locator(".source-links a").all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))
        self.assertEqual(self.page.locator(".related-grid a").count(), 6)
        report_download = self.page.get_by_role("link", name="Magyar jelentés letöltése")
        self.assertEqual(report_download.get_attribute("href"), "chat-control-report.md")
        self.assertEqual(report_download.get_attribute("download"), "chat-control-jelentes-hu.md")
        with self.page.expect_download() as download_info:
            report_download.click()
        self.assertEqual(download_info.value.suggested_filename, "chat-control-jelentes-hu.md")

    def test_encryption_postman_and_safeguard_graphics(self):
        self.assertEqual(self.page.locator(".postman").count(), 2)
        self.assertEqual(self.page.locator(".postman-satchel").count(), 2)
        self.assertEqual(self.page.locator(".postman-strap").count(), 2)
        self.assertEqual(self.page.locator(".postman-hand").count(), 4)
        encryption = self.page.locator("encryption-layers")
        self.assertEqual(encryption.get_by_role("tab").count(), 4)
        encryption.get_by_role("tab", name="4 · Lezárva a címzettig").click()
        self.assertEqual(encryption.locator(".service-answer strong").inner_text(), "NEM")
        self.assertIn("7F A9", encryption.locator(".provider-window").inner_text())
        self.assertIn("Találkozunk 6-kor?", encryption.locator(".recipient-message").inner_text())
        self.assertEqual(encryption.locator(".story-key.is-owned").count(), 2)
        self.assertEqual(
            encryption.locator(".story-key.is-owned").all_inner_texts(),
            ["Beszélgetés kulcsa", "Beszélgetés kulcsa"],
        )
        self.assertIn("E2EE", encryption.locator(".technical-name summary").inner_text())
        self.assertIn("saját rendszerében", encryption.locator(".story-legend").inner_text().lower())
        self.assertIn("nincs tartalomkulcsa", encryption.locator(".story-no-key").inner_text().lower())
        self.assertEqual(encryption.locator(".legend-service-screen").count(), 1)
        self.assertEqual(encryption.locator(".legend-window").count(), 0)
        self.assertNotIn("🔒", encryption.inner_text())
        self.assertNotIn("🔑", encryption.inner_text())
        encryption.get_by_role("tab", name="2 · A raktáros kulcsa").click()
        self.assertEqual(encryption.locator(".service-answer strong").inner_text(), "IGEN")
        self.assertIn("Családi fotók", encryption.locator(".provider-window").inner_text())
        self.assertEqual(encryption.locator(".story-key.is-owned").inner_text(), "Tárolási kulcs")
        encryption.get_by_role("tab", name="3 · A kulcs nálad marad").click()
        self.assertEqual(encryption.locator(".service-answer strong").inner_text(), "NEM")
        self.assertEqual(encryption.locator(".story-actor").count(), 2)
        self.assertEqual(encryption.locator(".story-recipient").count(), 0)
        self.assertEqual(encryption.locator(".story-key.is-owned").inner_text(), "Fájlkulcs")
        self.assertIn("nincs fájlkulcsa", encryption.locator(".story-no-key").inner_text().lower())
        encryption.get_by_role("tab", name="1 · Két zárt útszakasz").click()
        self.assertEqual(
            encryption.locator(".story-key.is-owned").all_inner_texts(),
            ["1. kapcsolat kulcsa", "1. és 2. kapcsolat kulcsa", "2. kapcsolat kulcsa"],
        )

        builder = self.page.locator("safeguard-builder")
        self.assertEqual(builder.locator("[data-safeguard]").count(), 6)
        builder.locator("[data-safeguard]").first.click()
        self.assertIn("önmagában kevés", builder.locator(".safeguard-status").inner_text())
        for button in builder.locator("[data-safeguard]").all()[1:]:
            button.click()
        self.assertIn("nem automatikus jóváhagyás", builder.locator(".safeguard-status").inner_text())

    def test_postman_satchel_pose_keyframes_and_reduced_motion(self):
        self.page.set_viewport_size({"width": 320, "height": 900})
        self.page.reload(wait_until="networkidle")
        artifact_dir = ROOT / "test-artifacts" / "regressions" / "postman-keyframes"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        def freeze_animations(selector, time_ms):
            self.page.evaluate(
                """({selector, time}) => {
                  const root = document.querySelector(selector);
                  root.getAnimations({subtree: true}).forEach(animation => {
                    animation.pause();
                    animation.currentTime = time;
                  });
                }""",
                {"selector": selector, "time": time_ms},
            )

        def assert_clear_satchel(postman, label, hand_extended=False):
            head_box = postman.locator(".postman-head").bounding_box()
            satchel = postman.locator(".postman-satchel")
            bag_box = satchel.bounding_box()
            hand_box = postman.locator(".postman-arm--front .postman-hand").bounding_box()
            mail_cues = satchel.evaluate(
                """element => {
                  const flap = getComputedStyle(element, '::before');
                  const mark = getComputedStyle(element, '::after');
                  return {
                    flapHeight: parseFloat(flap.height),
                    flapBorder: parseFloat(flap.borderBottomWidth),
                    markContent: mark.content,
                    markFontSize: parseFloat(mark.fontSize),
                  };
                }"""
            )
            self.assertGreaterEqual(
                bag_box["y"],
                head_box["y"] + head_box["height"] + 4,
                f"{label}: satchel rises into the face",
            )
            self.assertGreater(
                bag_box["width"],
                bag_box["height"],
                f"{label}: satchel reads as a square can instead of a wide mail bag",
            )
            self.assertGreaterEqual(
                mail_cues["flapHeight"],
                8,
                f"{label}: satchel flap is not visibly drawn",
            )
            self.assertGreaterEqual(
                mail_cues["flapBorder"],
                1,
                f"{label}: satchel flap has no visible separation",
            )
            self.assertIn(
                "✉",
                mail_cues["markContent"],
                f"{label}: satchel is missing its mail mark",
            )
            self.assertGreaterEqual(
                mail_cues["markFontSize"],
                12,
                f"{label}: satchel mail mark is too small to read",
            )
            if hand_extended:
                self.assertGreaterEqual(
                    hand_box["x"],
                    head_box["x"] + head_box["width"] + 2,
                    f"{label}: reaching hand remains too close to the face",
                )

        hero = self.page.locator(".hero-postman")
        for percent in (0, 23, 31, 50, 58, 70, 100):
            freeze_animations(".post-office", 5500 * percent / 100)
            assert_clear_satchel(hero, f"hero {percent}%", hand_extended=percent in (31, 50))
            self.page.locator(".post-office").screenshot(
                path=str(artifact_dir / f"hero-320-{percent:03d}.png")
            )

        story = self.page.locator("mail-story")
        story.locator('[data-step="0"]').click()
        for percent in (0, 30, 46, 55, 72, 88, 100):
            freeze_animations("mail-story .mail-illustration", 5400 * percent / 100)
            assert_clear_satchel(
                story.locator(".mail-postman"),
                f"mail opening {percent}%",
                hand_extended=percent in (46, 55, 72),
            )
            story.locator(".mail-illustration").screenshot(
                path=str(artifact_dir / f"story-open-320-{percent:03d}.png")
            )

        story.locator('[data-step="1"]').click()
        for percent in (0, 8, 18, 38, 48, 100):
            freeze_animations("mail-story .mail-illustration", 7200 * percent / 100)
            assert_clear_satchel(
                story.locator(".mail-postman"),
                f"locked-letter attempt {percent}%",
                hand_extended=percent in (18, 38),
            )
            story.locator(".mail-illustration").screenshot(
                path=str(artifact_dir / f"story-locked-320-{percent:03d}.png")
            )

        self.page.emulate_media(reduced_motion="reduce")
        self.page.reload(wait_until="networkidle")
        reduced_motion = self.page.eval_on_selector_all(
            ".postman, .postman *",
            """elements => {
              const toMilliseconds = value => {
                const trimmed = value.trim();
                return trimmed.endsWith('ms') ? parseFloat(trimmed) : parseFloat(trimmed) * 1000;
              };
              const durations = elements.flatMap(element =>
                getComputedStyle(element).animationDuration.split(',').map(toMilliseconds)
              );
              const iterations = elements.flatMap(element =>
                getComputedStyle(element).animationIterationCount.split(',').map(value =>
                  value.trim() === 'infinite' ? Infinity : parseFloat(value)
                )
              );
              return {
                maxDurationMs: Math.max(...durations),
                maxIterations: Math.max(...iterations),
              };
            }""",
        )
        self.assertLessEqual(reduced_motion["maxDurationMs"], 0.1)
        self.assertLessEqual(reduced_motion["maxIterations"], 1)
        self.assertEqual(self.page.locator(".postman-satchel").count(), 2)
        self.page.locator(".post-office").screenshot(
            path=str(artifact_dir / "hero-320-reduced-motion.png"), animations="disabled"
        )

    def test_legacy_language_page_redirects_to_hungarian_site(self):
        self.page.goto(f"{self.base_url}/languages.html?lang=en", wait_until="networkidle")
        self.page.wait_for_url("**/index.html")
        self.assertEqual(self.page.locator("html").get_attribute("lang"), "hu")
        self.assertIn("Felbontanád", self.page.locator("#hero-title").inner_text())
        self.page.set_viewport_size({"width": 390, "height": 844})
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)

    def test_public_page_is_hungarian_only(self):
        self.page.goto(f"{self.base_url}/?lang=en", wait_until="networkidle")
        self.assertEqual(self.page.locator("html").get_attribute("lang"), "hu")
        self.assertIn("Felbontanád", self.page.locator("#hero-title").inner_text())
        self.assertIn("Jelenlegi jogi helyzet", self.page.locator(".status-strip").get_attribute("aria-label"))
        self.assertIn("Öt külön szavazás", self.page.locator("#szavazas-title").inner_text())
        self.assertIn("aggódó állampolgár", self.page.locator("footer").inner_text().lower())
        self.assertEqual(self.page.locator("[data-language-toggle]").count(), 0)
        self.assertIsNone(self.page.evaluate("window.ChatControlI18n"))
        self.assertIsNone(self.page.evaluate("window.CHAT_CONTROL_FULL_LOCALES"))
        self.assertIn("/HU/", self.page.locator('.source-links a[href*="eur-lex"]').first.get_attribute("href"))
        self.page.set_viewport_size({"width": 390, "height": 844})
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)

    def test_hungarian_copy_is_responsive(self):
        checks = {
            "mail-story .mail-opening-label": "A szolgáltató hozzáférhet",
            ".private-talks h3": "A magánbeszélgetés attól még nem nyilvános, hogy digitális eszköz közvetíti",
            ".vote-chronology h3": "Mi történt, és melyik „Chat Controlról” döntöttek?",
            ".footer-brand div > span": "Egy aggódó állampolgár ismeretterjesztő oldala.",
        }
        self.page.set_viewport_size({"width": 390, "height": 844})
        self.page.goto(f"{self.base_url}/?lang=en", wait_until="networkidle")
        self.assertEqual(self.page.locator("html").get_attribute("lang"), "hu")
        for selector, hungarian in checks.items():
            self.assertEqual(self.page.locator(selector).inner_text().strip().casefold(), hungarian.casefold(), selector)
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        overflow_sources = self.page.evaluate(
            """() => [...document.querySelectorAll('body *')].map(element => {
              const rect = element.getBoundingClientRect();
              return { tag: element.tagName.toLowerCase(), className: element.className || '', text: (element.textContent || '').trim().slice(0, 90), left: Math.round(rect.left), right: Math.round(rect.right) };
            }).filter(item => item.left < -1 || item.right > document.documentElement.clientWidth + 1).slice(0, 12)"""
        )
        self.assertLessEqual(overflow, 1, f"hu: {overflow_sources}")

    def test_previous_language_implementations_are_archived(self):
        multilingual = ROOT / "backups" / "multilingual-15-language-snapshot-2026-07-14.tar.gz"
        bilingual = ROOT / "backups" / "hungarian-english-site-snapshot-2026-07-14.tar.gz"
        self.assertTrue(multilingual.is_file())
        self.assertTrue(bilingual.is_file())
        with tarfile.open(multilingual) as backup:
            multilingual_names = set(backup.getnames())
        with tarfile.open(bilingual) as backup:
            bilingual_names = set(backup.getnames())
        self.assertTrue({
            "language-data.js",
            "full-i18n.js",
            "locales/full-west.js",
            "locales/full-south.js",
            "locales/full-east.js",
            "locales/full-east-quiz-semantic.js",
        }.issubset(multilingual_names))
        self.assertTrue({
            "index.html",
            "full-i18n.js",
            "locales/full-english-ui.js",
            "locales/full-feedback-ui.js",
            "language-page.js",
        }.issubset(bilingual_names))


if __name__ == "__main__":
    unittest.main()
