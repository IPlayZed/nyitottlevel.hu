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
        self.assertEqual(self.page.locator("main > section").count(), 12)
        self.assertEqual(self.page.locator("[data-language-toggle]").count(), 0)
        self.assertEqual(self.page.locator('script[src^="locales/"]').count(), 0)
        self.assertEqual(self.page.locator('script[src="full-i18n.js"]').count(), 0)
        self.assertIn("aggódó állampolgár", self.page.locator("footer").inner_text().lower())

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
        self.page.locator("mail-story [data-mail-next]").click()
        self.assertIn("végpontok közötti titkosítás", self.page.locator("mail-story h3").inner_text())
        mail_story = self.page.locator("mail-story")
        self.assertEqual(mail_story.locator(".mail-object.is-e2ee").count(), 1)
        self.assertIn("7F A9", mail_story.locator(".mail-note-cipher").inner_text())
        self.assertEqual(mail_story.locator(".mail-e2ee-no-key").count(), 1)
        self.assertEqual(mail_story.locator(".mail-e2ee-key").count(), 1)
        self.assertEqual(mail_story.locator(".mail-e2ee-key-traveller").count(), 1)
        comparison = mail_story.locator(".mail-key-comparison").inner_text().lower()
        self.assertIn("kulcs nélkül", comparison)
        self.assertIn("a címzett kulcsával", comparison)
        explanation = mail_story.locator(".mail-copy").inner_text().lower()
        self.assertIn("kulcs nélkül", explanation)
        self.assertIn("címzett készüléke", explanation)
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
        self.assertIn("teljes levelezés", self.page.locator("detection-lab .lab-copy h3").inner_text())
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

    def test_detection_math_invariants_and_zero_alert_state(self):
        cases = (
            (0, 0, 0),
            (0.1, 90, 0.5),
            (1, 70, 1),
            (50, 50, 50),
            (100, 100, 100),
        )
        for prevalence, sensitivity, false_rate in cases:
            with self.subTest(prevalence=prevalence, sensitivity=sensitivity, false_rate=false_rate):
                self.page.locator("#prevalence").fill(str(prevalence))
                self.page.locator("#sensitivity").fill(str(sensitivity))
                self.page.locator("#falseRate").fill(str(false_rate))
                counts = [
                    int(self.page.locator(f"detection-lab [{field}]").inner_text().replace("\xa0", "").replace(" ", ""))
                    for field in ("data-tp", "data-fn", "data-fp", "data-tn")
                ]
                positives = round(10000 * prevalence / 100)
                self.assertEqual(sum(counts), 10000)
                self.assertEqual(counts[0] + counts[1], positives)
                self.assertEqual(counts[2] + counts[3], 10000 - positives)

        self.page.locator("#prevalence").fill("0")
        self.page.locator("#sensitivity").fill("0")
        self.page.locator("#falseRate").fill("0")
        self.assertEqual(self.page.locator("detection-lab [data-ppv]").inner_text(), "Nem értelmezhető")
        self.assertIn("Nincs riasztás", self.page.locator("detection-lab [data-rate-summary]").inner_text())
        self.assertIn("Nincs riasztás", self.page.locator("detection-lab [data-alert-caption]").inner_text())

        self.page.locator("#prevalence").fill("0.1")
        self.page.locator("#sensitivity").fill("90")
        self.page.locator("#falseRate").fill("0.5")
        rare_cards = self.page.locator("detection-lab .rare-count")
        self.assertEqual(rare_cards.count(), 4)
        self.assertEqual(rare_cards.nth(0).locator(".rare-dot").count(), 9)
        self.assertEqual(rare_cards.nth(1).locator(".rare-dot").count(), 1)
        self.assertEqual(rare_cards.nth(2).locator(".rare-dot").count(), 20)
        self.assertEqual(rare_cards.nth(2).locator(".rare-more").count(), 1)
        self.assertEqual(rare_cards.nth(0).get_attribute("aria-label"), "Valódi találat: 9")

    def test_report_source_count_is_precise_without_claiming_every_source_is_primary(self):
        report = (ROOT / "chat-control-report.md").read_text(encoding="utf-8")
        urls = set(re.findall(r"https?://[^\s)>]+", report))
        self.assertEqual(len(urls), 61)
        banner = self.page.locator(".action-banner h3").inner_text()
        self.assertIn("61 egyedi hivatkozott forrással", banner)
        self.assertNotIn("61 elsődleges", banner)

    def test_abuse_paths_and_documented_cases(self):
        self.assertEqual(self.page.locator("abuse-simulator [data-abuse]").count(), 6)
        self.page.get_by_role("tab", name="Forrásvédelem").click()
        self.assertIn("öncenzúrát", self.page.locator("abuse-simulator .abuse-path").inner_text())
        self.assertEqual(self.page.locator("abuse-history .history-case").count(), 9)
        self.page.get_by_role("button", name="Vállalati hozzáférés").click()
        self.assertEqual(self.page.locator("abuse-history .history-case").count(), 2)
        self.assertIn("Twitter", self.page.locator("abuse-history").inner_text())

    def test_vote_quiz_dialog_and_motion_control(self):
        self.page.get_by_role("button", name="Számoljuk meg a 314-et").click()
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
        self.assertTrue(self.page.get_by_role("button", name="Új 10 kérdés").is_visible())
        self.page.get_by_role("button", name="Új 10 kérdés").click()
        second_ids = self.page.evaluate("() => document.querySelector('myth-quiz').questions.map(question => question.id)")
        self.assertEqual(len(set(first_ids).intersection(second_ids)), 0)

    def test_mobile_navigation_and_layout(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        motion = self.page.locator("#motionToggle")
        self.assertTrue(motion.is_visible())
        self.assertEqual(motion.locator(".button-label").inner_text(), "Animáció leállítása")
        motion.click()
        self.assertEqual(motion.locator(".button-label").inner_text(), "Animáció indítása")
        self.assertEqual(motion.get_attribute("aria-pressed"), "true")
        self.page.locator("#menuButton").click()
        self.assertEqual(self.page.locator("#menuButton").get_attribute("aria-expanded"), "true")
        self.assertTrue(self.page.locator("#mobileNav").is_visible())
        self.page.locator("#mobileNav a").first.click()
        self.assertEqual(self.page.locator("#menuButton").get_attribute("aria-expanded"), "false")
        overflow = self.page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        self.assertLessEqual(overflow, 1)
        self.assertGreaterEqual(self.page.locator("#menuButton").bounding_box()["width"], 44)

    def test_action_dialog_and_source_links(self):
        self.page.get_by_role("button", name="Levélminta megnyitása").click()
        self.assertTrue(self.page.locator("#letterDialog").is_visible())
        self.assertIn("végpontok közötti titkosítás", self.page.locator("#letterTemplate").input_value())
        self.assertEqual(self.page.locator(".source-links a").count(), 6)
        self.assertIn("/HU/", self.page.locator('.source-links a[href*="eur-lex"]').first.get_attribute("href"))
        for link in self.page.locator(".source-links a").all():
            self.assertTrue(link.get_attribute("href").startswith("https://"))
        self.assertEqual(self.page.locator(".related-grid a").count(), 6)

    def test_encryption_postman_and_safeguard_graphics(self):
        self.assertEqual(self.page.locator(".postman").count(), 2)
        encryption = self.page.locator("encryption-layers")
        self.assertEqual(encryption.get_by_role("tab").count(), 4)
        encryption.get_by_role("tab", name="Végponttól végpontig · E2EE").click()
        self.assertIn("nem kap tartalomfeloldó kulcsot", encryption.locator(".encryption-copy").inner_text().lower())
        self.assertEqual(encryption.locator(".crypto-key-chip.has-key").count(), 2)
        self.assertNotIn("🔒", encryption.inner_text())
        self.assertNotIn("🔑", encryption.inner_text())
        encryption.get_by_role("tab", name="Tároláskor · szolgáltatói kulcs").click()
        self.assertIn("saját kulcsával feloldhatja", encryption.locator(".encryption-copy").inner_text().lower())

        builder = self.page.locator("safeguard-builder")
        self.assertEqual(builder.locator("[data-safeguard]").count(), 6)
        builder.locator("[data-safeguard]").first.click()
        self.assertIn("önmagában kevés", builder.locator(".safeguard-status").inner_text())
        for button in builder.locator("[data-safeguard]").all()[1:]:
            button.click()
        self.assertIn("nem automatikus jóváhagyás", builder.locator(".safeguard-status").inner_text())

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
            "mail-story .mail-opening-label": "A postás felnyitja",
            ".private-talks h3": "A magánbeszélgetés attól még nem nyilvános, hogy digitális eszköz közvetíti",
            ".vote-chronology h3": "Mi történt, és melyik „Chat Controlról” döntöttek?",
            ".footer-brand div > span": "Aggódó állampolgári ismeretterjesztő oldal.",
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
