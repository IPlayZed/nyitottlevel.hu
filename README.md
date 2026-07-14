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
- `tests/test_mobile_profiles.py` — interactive layout checks across every unique viewport in Playwright's built-in Chromium mobile-device catalogue; it captures ten state screenshots per viewport and writes a geometry/font-size analysis manifest
- `tests/test_desktop_profiles.py` — stateful visual checks for the documented desktop support matrix

Previous multilingual builds are preserved locally under the ignored `backups/` directory. Neither the archives nor the superseded localisation runtime files are included in the public repository.

## Testing

The test suite uses the system-installed Chromium, so it does not download a separate browser build.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m unittest tests/test_site.py -v
.venv/bin/python -m unittest tests/test_mobile_profiles.py -v
.venv/bin/python -m unittest tests/test_desktop_profiles.py -v
```

The mobile-profile run writes ignored artifacts to `test-artifacts/mobile/`: top-of-page, the hero envelope’s open state, paused-motion header, action cards, both phases of mail step 2, user-key encryption, rare-result magnification, mass-surveillance mode, and the filtered help directory for every unique viewport. `manifest.json` records the tested state, screenshot paths, font-size floors, overlap clearances, route-label margins, horizontal overflow, and browser errors. These generated artifacts are intentionally excluded from Git.

The desktop-profile run applies the same stateful visual review to the documented 1024, 1366, 1440, 1920, and 2560-pixel desktop widths. Its ignored screenshots and analysis manifest are written to `test-artifacts/desktop/`.

## Feedback

The site links to a Hungarian GitHub issue form for factual corrections, copy feedback, accessibility reports, and technical problems:

<https://github.com/IPlayZed/nyitottlevel.hu/issues/new?template=feedback_hu.yml>

GitHub issues are public. The form warns contributors not to include personal, confidential, or sensitive information.

## GitHub Pages

1. Push the files to the root of a GitHub repository.
2. Open **Settings → Pages** in the repository.
3. Choose **Deploy from a branch**.
4. Select the `main` branch and the `/ (root)` directory.

The repository is configured for branch-based Pages deployment from `main` at the repository root. All internal asset links are relative, so the site works under the GitHub project subpath.

## Cloudflare Pages

Connect the repository through Git integration and use these settings:

- Framework preset: `None`
- Production branch: `main`
- Build command: `exit 0`
- Build output directory: `.`

The site has no server-side runtime or required environment variables. Cloudflare Pages can publish the static files directly from the repository root and provide automatic branch and pull-request preview URLs.

## Maintenance

The research cutoff date is displayed on the site. After a relevant legal or political development, update both the date and the corresponding status explanations. Keep repository and developer documentation in English; public editorial content is currently maintained in Hungarian in the semantic HTML and interactive components.

## License

The project is licensed under the GNU Affero General Public License, version 3 or any later version (`AGPL-3.0-or-later`). See [`LICENSE`](LICENSE).
