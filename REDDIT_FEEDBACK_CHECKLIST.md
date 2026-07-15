# Reddit Feedback Checklist

Source thread: [r/hungary — Hungarian Chat Control explainer](https://www.reddit.com/r/hungary/comments/1uwniq2/)

Use this file as the implementation checklist. Complete an item by changing `[ ]` to `[x]`; optionally strike completed text with `~~text~~` after verification.

## Review protocol

- Each review batch is committed separately on the `reddit-feedback-review` branch.
- A batch may combine only closely related checklist lines that produce one coherent user-visible change.
- The implementation pauses after every batch so the site owner can inspect the diff and rendered result.
- Requested corrections stay in the same batch and commit history until that batch is accepted.
- Checklist items are marked complete only after implementation, focused tests, and visual inspection pass.
- No batch is merged into `main` or deployed before explicit approval.
- The final release gate runs only after every preceding batch has been accepted.

## Editorial balance and fast orientation

- [ ] Add a directly linkable “Common misconceptions” section for visitors who will not read the full page.
- [ ] Address the claim “I have nothing to hide.”
- [ ] Address the claim “Only criminals are affected.”
- [ ] Address the claim “Providers already read every message anyway.”
- [ ] Address the claim “Encryption and mathematics can simply be banned.”
- [ ] Explain the distinction between technically preventing encryption and legally restricting or selectively enforcing its use.
- [ ] Present the strongest good-faith case for the proposed regulation before responding to it.
- [ ] Explain why detecting smaller-scale offenders and grooming can matter, not only catching sophisticated “big fish.”
- [ ] Explain what automated provider-side scanning already exists today and how it differs from a general legal scanning obligation.
- [ ] Explain supporters’ argument that correctly implemented end-to-end encryption can create a detection gap for providers.
- [ ] Explain opponents’ counterargument that sophisticated offenders can move to other tools while ordinary users remain exposed to scanning.
- [ ] Explain scope-creep risk: how an infrastructure created for one target could later be expanded to other content or conduct.
- [ ] Explain false-positive risks for lawful intimate images, including uncertain age estimation.
- [ ] Explain why targeted investigation and indiscriminate scanning are not equivalent.
- [ ] Add practical, less intrusive child-protection alternatives instead of discussing only why Chat Control is risky.
- [ ] Explain what parents, devices, platforms, and existing law can currently do about children under the platform age limit.
- [ ] Clearly separate age assurance, parental controls, platform access restrictions, and private-message scanning.
- [ ] Ensure the page cannot reasonably be read as saying that online child sexual abuse or grooming is unimportant.
- [ ] Re-run the political-neutrality review after adding the supporting arguments and responses.

Reddit references: [missing opposing arguments](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxl8x73/), [second request for counterarguments](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxlq7xh/), [supporting case for detection](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxmqlzm/), [privacy and scope-creep concerns](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxn1jj2/)

## Postal analogy and technical explanations

- [ ] Define one consistent mapping between a letter, envelope, message content, encryption, key, sender, recipient, provider, and authority.
- [ ] Stop switching between letters, files, images, and generic data without an explicit transition.
- [ ] Decide whether the encryption story uses a sealed envelope alone or a “special envelope plus matching opener” metaphor.
- [ ] If keys remain in the metaphor, explain once why a physical key appears in an envelope story.
- [ ] Keep technical terms such as ciphertext outside the primary analogy or reveal them only in an optional technical note.
- [ ] Review every mail-story step for contradictions between the illustration and its explanation.
- [ ] Review the provider-key storage story against the final postal metaphor.
- [ ] Review the user-key storage story against the final postal metaphor.
- [ ] Review the E2EE story against the final postal metaphor.
- [ ] Replace or rework the postal-stamp analogy for hashing if it conflicts with the sealed-envelope model.
- [ ] Evaluate a photograph-versus-copy analogy for exact and perceptual hashing.
- [ ] Explain explicitly that a hash or perceptual fingerprint can be compared without being the original image itself.
- [ ] Re-test the redesigned analogies with a layperson reviewer who has not read the technical report.

Reddit reference: [detailed analogy critique](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxl8941/)

## Voting history and timeline

- [ ] Add or more prominently explain the 7 July 2026 accelerated-procedure vote.
- [ ] Explain exactly what the 7 July vote did and did not decide.
- [ ] Explain exactly what the 9 July vote did and did not decide.
- [ ] Show why the 9 July rejection required an absolute majority of all MEPs rather than a simple majority of votes cast.
- [ ] Explain the relationship between the accelerated procedure, attendance, and the later absolute-majority threshold without presenting inference as proven intent.
- [ ] Make it easy to compare how individual MEPs voted on 7 July and 9 July.
- [ ] Highlight cases where an MEP or group voted differently in the two July votes.
- [ ] Verify the two July vote datasets against the official named roll-call records again.
- [ ] Add a short plain-language introduction before the two July vote cards.
- [ ] Test the revised chronology with readers who do not know EU legislative procedure.

Reddit reference: [request to include and contextualize the first July vote](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxkq2on/)

## Help and research directory

- [ ] Re-audit every organization in the “Who can I contact or research?” directory.
- [ ] State whether each organization offers individual help, accepts complaints, conducts research, advocates, or merely publishes official material.
- [ ] Re-check whether NAIH is relevant to each scenario described, including cases where processing is explicitly authorized by law.
- [ ] Remove any implication that NAIH can invalidate EU legislation or provide remedies outside its actual competence.
- [ ] Re-check whether NBSZ should appear as a help or research destination at all.
- [ ] If NBSZ remains, label its institutional role precisely and do not present it as an independent privacy advocate.
- [ ] Prioritize Hungarian civil-rights and privacy organizations where they have a real role.
- [ ] Keep EDRi and primary EU legal sources clearly categorized as advocacy/research and official-law resources.
- [ ] Have a Hungarian privacy or legal expert review the final organization descriptions before marking this section complete.

Reddit reference: [directory criticism](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxl8941/)

## Report formats and language quality

- [ ] Keep the Markdown research report as the editable/source version.
- [ ] Provide a rendered HTML version of the complete report.
- [ ] Provide an accessible downloadable PDF version of the complete report.
- [ ] Ensure the HTML and PDF versions are generated from the same reviewed source to prevent content drift.
- [ ] Add document title, version date, source count, and citizen-authored disclaimer to every format.
- [ ] Verify links and internal anchors in the HTML report.
- [ ] Verify selectable text, heading structure, page breaks, tables, and clickable links in the PDF.
- [ ] Run another full Hungarian naturalness review over the public page after the new sections are added.
- [ ] Replace any wording that sounds translated, forced, bureaucratic, or unnecessarily technical.
- [ ] Run another layperson comprehension review independently of the language review.

Reddit reference: [Markdown usability and wording criticism](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxl8941/)

## Visual details

- [ ] Redesign the postman’s hand-held object or pose so it cannot look like inhaling from a fuel can.
- [ ] Inspect the postman at every animation keyframe, not only the resting frame.
- [ ] Verify that the revised postman still reads clearly at 320 px width.
- [ ] Preserve the existing color palette unless a contrast or accessibility test requires a change.
- [ ] Re-run reduced-motion checks after changing the animation.
- [ ] Re-run all mobile and desktop screenshot states after changing the character.

Reddit reference: [postman joke and color-palette praise](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxkq217/)

## Transparency and trust

- [ ] Add a concise methodology note explaining which parts were researched, written, reviewed, and generated with AI assistance.
- [ ] Explain that the technical analysis was directed by an IT professional while legal claims were researched and source-checked.
- [ ] Link to the public source repository and feedback process from the methodology note.
- [ ] Explain how factual corrections will be documented.
- [ ] Avoid implying professional legal or journalistic review where none occurred.
- [ ] Keep the nonpartisan disclaimer prominent and distinguish it from the author’s personal political identity.

Reddit reference: [question about AI contribution and authorship](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxkk8jo/)

## Possible follow-up project

- [ ] Decide whether age assurance belongs on this site or should be a separate explainer.
- [ ] If pursued, research age declaration, age estimation, identity-based verification, device-level child accounts, parental controls, and platform bans separately.
- [ ] Compare circumvention risks, privacy costs, exclusion risks, and enforcement limits for each age-assurance approach.
- [ ] Do not merge the age-assurance project into Chat Control without clearly separating the two legal and technical questions.

Reddit reference: [request for a Hungarian age-verification explainer](https://www.reddit.com/r/hungary/comments/1uwniq2/k%C3%A9sz%C3%ADtettem_magyarul_egy_bemutat%C3%B3_oldalt_a_chat/oxmdctk/)

## Release gate for the feedback round

- [ ] Every implemented factual claim has a directly supporting source.
- [ ] Hungarian-language sources are preferred where an equally authoritative version exists.
- [ ] The factual reviewer returns PASS.
- [ ] The technical and mathematical reviewer returns PASS.
- [ ] The Hungarian language reviewer returns PASS.
- [ ] The independent layperson reviewer returns PASS.
- [ ] The security reviewer returns PASS.
- [ ] Functional tests pass.
- [ ] The complete mobile-profile visual suite passes with eight workers.
- [ ] The complete desktop-profile visual suite passes.
- [ ] Representative screenshots are batch-reviewed for regressions.
- [ ] External-link validation reports no broken destinations.
- [ ] The production GitHub Pages files match the reviewed release.
- [ ] Production desktop and mobile interaction smoke tests pass.
