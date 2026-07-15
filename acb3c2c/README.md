# Nyitott Levél — Chat Control, clearly explained

An interactive educational site about the temporary and proposed EU rules commonly referred to as “Chat Control”. It explains the different layers of encryption and key ownership, content detection, false-positive and false-negative results, EU decision-making, and the risk of political misuse. The public site is currently Hungarian-only.

The site is static and runs without a build step. Its reactive interface uses browser-native Web Components, so it does not load a third-party JavaScript framework, hosted runtime, or tracking code.

Public site: <https://iplayzed.github.io/nyitottlevel.hu/>

Public repository: <https://github.com/IPlayZed/nyitottlevel.hu>

## Local development

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Project files

- `index.html` — the complete story and semantic page structure
- `styles.css` — responsive visual system, animations, and accessible states
- `app.js` — Web Components and page-level interactions
- `quiz-data.js` — 100 reviewed questions across ten topics
- `vote-data.js` — five roll-call votes with 2,901 individual positions
- `scripts/build_vote_data.py` — reproducible generation of static vote data from reviewed roll-call records
- `chat-control-report.md` — detailed research report and bibliography
- `tests/test_site.py` — Playwright-based end-to-end browser tests
- `tests/test_mobile_profiles.py` — interactive layout checks across every unique viewport in Playwright's built-in Chromium mobile-device catalogue; it captures twenty-three state screenshots per viewport, rejects black/compositor-corrupted frames, and writes a geometry/font-size analysis manifest
- `tests/test_desktop_profiles.py` — stateful visual checks for the documented desktop support matrix
- `tests/test_firefox_profiles.py` — focused Firefox checks for the postal animation, consistent key labels, and encryption-story layouts at five representative viewports
- `scripts/run_visual_tests.py` — parallel visual-test runner that shards profiles across isolated browser processes and merges their manifests deterministically

Previous multilingual builds are preserved locally under the ignored `backups/` directory. Neither the archives nor the superseded localisation runtime files are included in the public repository.

## Testing

The Chromium suites use the system-installed browser. The focused Firefox suite uses Playwright's tested Firefox build, which must be installed once after the Python dependencies.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install firefox
.venv/bin/python -m unittest tests/test_site.py -v
.venv/bin/python -m unittest tests/test_mobile_profiles.py -v
.venv/bin/python -m unittest tests/test_desktop_profiles.py -v
.venv/bin/python -m unittest tests/test_firefox_profiles.py -v
```

The three visual suites run in isolated parallel processes. Mobile testing uses up to eight workers by default; desktop and Firefox testing use five because they currently have five profiles each. The worker count can be lowered on memory-constrained machines:

```bash
.venv/bin/python scripts/run_visual_tests.py all
.venv/bin/python scripts/run_visual_tests.py mobile --workers 2
```

Each process owns its Playwright driver, browser instance, loopback server, and disjoint profile shard. This avoids sharing Playwright's synchronous API across threads. Shard manifests are merged atomically in profile order only after every process succeeds. The runner also writes a `review.html` gallery that groups every viewport by screenshot state, so visual comparisons can be reviewed as batches instead of one image at a time.

The mobile-profile run writes ignored artifacts to `test-artifacts/mobile/`: top-of-page, the hero envelope’s open state, paused-motion header, action cards, both phases of mail step 2, the redesigned service-inspection and before-sealing mail scenes, all four encryption stories, rare-result magnification, mass-surveillance mode, the filtered help directory, the selected vote, and the safeguards for every unique viewport. It also measures label containment in every encryption story. `manifest.json` records the tested state, screenshot paths, font-size floors, overlap clearances, encryption-story margins, horizontal overflow, and browser errors. These generated artifacts are intentionally excluded from Git.

The desktop-profile run applies the same stateful visual review to the documented 1024, 1366, 1440, 1920, and 2560-pixel desktop widths, captures all four encryption modes plus navigation, institution, and voting states, and rejects black/compositor-corrupted frames. Its ignored screenshots and analysis manifest are written to `test-artifacts/desktop/`.

The focused Firefox run freezes every meaningful hero-envelope keyframe at five representative viewports, verifies that the label remains inside the animated paper, confirms that the recipient key never travels back to the service, and captures the postal legend plus all four encryption modes. Its ignored screenshots and manifest are written to `test-artifacts/firefox/`.

## Feedback

The site links to a Hungarian GitHub issue form for factual corrections, copy feedback, accessibility reports, and technical problems:

<https://github.com/IPlayZed/nyitottlevel.hu/issues/new?template=feedback_hu.yml>

GitHub issues are public. The form warns contributors not to include personal, confidential, or sensitive information.

## GitHub Pages

1. Push the files to the root of a GitHub repository.
2. Open **Settings → Pages** in the repository.
3. Choose **Deploy from a branch**.
4. Select the `main` branch and the `/ (root)` directory.
5. After GitHub provisions the certificate, enable **Enforce HTTPS** in the same Pages settings.

The repository is configured for branch-based Pages deployment from `main` at the repository root. All internal asset links are relative, so the site works under the GitHub project subpath. GitHub documents HTTPS support and HTTPS enforcement for both `github.io` sites and correctly configured custom domains.

GitHub Pages does not provide repository-controlled custom response headers. The site therefore carries its portable Content Security Policy and no-referrer policy in HTML meta tags, keeps all runtime assets local, rejects unsafe dynamic URLs, and opens external sources without a referrer. The production acceptance test must confirm that HTTP redirects to HTTPS and that every CSS, JavaScript, image, and document request remains on HTTPS. Framing protection such as a response-header `frame-ancestors` directive cannot be guaranteed on branch-based GitHub Pages; use a header-configurable host if that requirement becomes mandatory.

## Maintenance

The research cutoff date is displayed on the site. After a relevant legal or political development, update both the date and the corresponding status explanations. Keep repository and developer documentation in English; public editorial content is currently maintained in Hungarian in the semantic HTML and interactive components.

## License

The project is licensed under the GNU Affero General Public License, version 3 or any later version (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE).
