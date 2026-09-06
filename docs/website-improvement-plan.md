# Website improvement plan

Review date: 5 September 2026. Scope: the public catalog, study readers, My Submissions, discussions, document publishing, and retrieval architecture.

## Recommendation

Make long studies easier to navigate, resume, search, and verify before introducing an AI assistant. Keep the existing static publishing architecture. Fix the authentication and rendering boundaries first; add passage search before deciding whether semantic retrieval earns its cost. A vector database will not resolve the reading experience by itself.

This plan records a source review and sampled live browser checks, not a penetration test or an authenticated production submission test. Browser measurements are samples, not field-performance guarantees.

## Baseline and findings

- The catalog contains 27 entries: 8 released, 5 drafts, and 14 ongoing. The 13 available studies contain approximately 175,000 whitespace-separated words, including references and markup. The largest documents are about 34,000 words each.
- All 26 catalog HTML/PDF destinations returned HTTP 200 in the sampled link check. Sampled HTML was Brotli-compressed and served from Cloudflare cache. Approximate transferred HTML sizes: catalog 28 KB, submission portal 29 KB, ontology reader 100 KB; decoded sizes are substantially larger.
- HSTS, CSP, frame restrictions, and MIME sniffing protection are present on the sampled live site. These are useful defenses, but do not replace safe rendering or request authorization.
- The stored August 30 RUM baseline covers only 45 page views, including 34 catalog views. It reports catalog p75 LCP of 2.6 seconds and TTFB of 1.296 seconds. The reported CLS of 1.0 and INP of zero need investigation; zero INP in this sample does not establish good responsiveness. Collect fresh, segmented data before drawing conclusions.
- GitHub OAuth used a constant authorization state and did not compare the callback state. Its session helper could place the GitHub access token in a signed, readable cookie when KV was absent.
- Cookie-authenticated write routes relied on CORS/SameSite without a common request-origin and JSON enforcement boundary. Personalized API responses lacked an explicit private/no-store policy.
- Discussion magic tokens were selected and then marked used in separate statements, allowing simultaneous consumption. Tokens were stored in directly usable form.
- Markdown rendering accepted raw active HTML; Mermaid used loose security mode. Generated page metadata also needs protection against closing-script text. PDF rendering should deny arbitrary network and local-file access.
- The reader’s Next section control is disabled above the first section. Only top-level headings receive sticky-toolbar anchor offsets. Explicit light mode can inherit the browser’s dark canvas, and narrow screens can overflow. Catalog date sorting passes human-formatted IST strings directly to Date.parse.
- My Submissions already has autosave, previews, revision workflows, and filters. Its single local draft key and limited preview fidelity remain substantial future reliability work.

## Delivery phases

Estimates are indicative engineering effort for one developer, subject to review and testing. Phases 1 and 2 have been implemented; Phase 2 merged in PR #400. Phase 3 is authorized and recorded below. Phases 4–6 remain recommendations.

| Phase | Deliverables | Acceptance criteria | Estimate |
| --- | --- | --- | --- |
| 1 — Correct defects and security boundaries | Verified OAuth state and PKCE; server-side GitHub tokens; origin/JSON write checks; private API caching; atomic, hashed magic tokens; safe author-content rendering; reader anchors, initial navigation, theme and overflow; reliable date sorting | Attack/regression tests pass; both Workers bundle; catalog generation verifies; representative PDF pipeline checks pass; mobile and desktop browser checks pass | 1–2 weeks |
| 2 — Reader essentials | Persistent collapsible contents, current section, reading preferences, resume position, named bookmarks, mobile drawers | Reader can leave and resume a precise passage; keyboard and mobile navigation remain usable; preferences survive reload | 1–2 weeks |
| 3 — Find and verify | Full-text passage search, stable passage links, citation/source previews, diagram and table viewing | Exact terms and phrases find cited passages; users can inspect the supporting source and return without losing their place | 1–2 weeks |
| 4 — Contributor reliability | Independent draft storage, visible save state, recovery, production-matching preview, actionable feedback and retries | Switching study/account/artifact cannot overwrite another draft; interrupted submission can recover; reviewer feedback identifies the action needed | 1–2 weeks |
| 5 — Deeper study tools | Highlights, notes and export, offline reading, optional selected-text read-aloud | Notes remain tied to versioned passages; export works without lock-in; offline availability and audio limitations are clear | 1–2 weeks |
| 6 — Semantic retrieval pilot | Curated corpus, hybrid retrieval, evaluation set, optional answers with citations | Retrieval improves measured tasks over lexical search; citations support claims; ambiguous and unsupported questions produce appropriate abstention | 1–2 weeks |

## Long-study reading experience

On desktop, use a collapsible contents column, a readable central text column, and an optional sources/notes panel. Expand only the current section’s subsections. On mobile, use drawers for contents and tools, preserving room for the text. Keep browser Back, Find, selection, copy, deep links, and print working normally.

1. **Orientation and resumption:** show the current section, position within it, and an approximate section reading time. Save a stable passage identifier plus offset, rather than only a percentage. Offer an explicit Resume action and named bookmarks without requiring an account. Scrolling must not be described as understanding or completing an argument.
2. **Comfort:** adjustable font size, line height and width; light, dark and sepia preferences. Screen paragraph alignment should be evaluated with readers; keep the existing print contract separate. Controls need visible focus and adequate touch targets.
3. **Finding material:** in-study search with excerpts, match counts and next/previous results; cross-study search with document, source type, language and status filters. Preserve exact Sanskrit/Hindi terms and allow transliteration aliases.
4. **Verification:** open citations beside the passage, showing source title, edition, language, page or timestamp, and permitted excerpts. Provide Copy citation and Copy passage link. Let users enlarge diagrams and tables without losing their place.
5. **Active study:** highlights, private notes, a collected-notes view and Markdown/JSON export. Tie annotations to a document version and warn when their passage changes. Local storage can be the default; sync should be optional and explicit.
6. **Alternative access:** offline reading or EPUB, selected-text read-aloud with sentence highlighting and pronunciation support, and accessible descriptions of diagrams. These are optional tools, loaded on demand.
7. **Reading routes:** add editor-reviewed guides outside the scholarly essay: prerequisites, full argument, comparison, and open problems. Summaries must preserve the distinction between the project’s interpretation and primary texts. Do not collapse satta, Brahman, physical space, or other traditions into convenient but misleading synonyms.

## My Submissions and discussions

Use draft keys that include account, study, artifact type and revision. Show the last successful save, unsaved state, storage errors, recovered drafts and a deliberate shared-device cleanup action. Keep a recoverable copy before overwriting or submitting. Preview should use the same safe Markdown, math, table and diagram contract as production.

Each submission card should answer: what is this, what is its state, who acts next, and what can I do now? Separate publication status (ongoing/draft/released) from workflow status (submitted/review requested/changes requested/merged). Surface actionable review failures and before/after differences in the portal. Use bounded retries and concurrency protection; avoid creating duplicate requests after an uncertain network result.

Explain that GitHub is used for contributions and email sign-in for discussions; retain the pending action across authentication. Make public submission visibility and notification preferences clear. Give realistic response expectations instead of implying instant review.

Allow discussions to quote and link a passage. Preserve unsent comment text across sign-in. Add report/moderation workflows and notification controls. Further security work includes discussion-session revocation, per-user/IP quotas, replay/abuse monitoring, and a reviewed retention policy.

## Other pages, accessibility and performance

- Keep navigation, theme and terminology consistent across catalog, reader, contribution and reference pages. Make teaching decks and presenter companions easier to discover.
- Build a curated reference library with edition, language, translation status and canonical publisher links. Clearly label working translations and unreviewed transcripts.
- Maintain existing canonical URLs, sitemap, feeds and metadata. Give the API a practical quickstart before protocol detail.
- Measure catalog, reader and portal separately, on mobile and desktop. Target p75 LCP ≤2.5 s, INP ≤200 ms and CLS ≤0.1 with adequate samples. Audit the surprising stored CLS result before assigning a cause.
- Pre-render diagrams where practical; align browser and PDF Mermaid versions. Give images dimensions, defer below-fold images, and load optional tools only when opened. Extract stable shared assets with content hashes when measurement justifies it.
- Avoid redundant catalog reconstruction and unnecessary dashboard refreshes. Consider incremental/webhook updates and bounded backoff. Keep public comment loading independent of optional authentication work.
- Test WCAG 2.2 AA, including keyboard-only operation, visible focus, labels, contrast, reduced motion and 320 CSS-pixel reflow. Prefer 44-pixel primary touch controls; WCAG’s 24-pixel minimum has defined exceptions. Tables and diagrams may scroll within their own regions.

## Do we need a vector database?

**Not for Phase 1, and not to make the reader usable.** Start with a static full-text index such as Pagefind. Exact terms, names, section references and quotations are important in this corpus and should not depend on an embedding model.

A vector index becomes useful for conceptual or multilingual questions that use different words from the text, related-passage discovery, and retrieval for a cited answer assistant. It is an additional search index, not the document store, a truth checker, or a replacement for lexical search. Use hybrid lexical/vector retrieval and evaluate whether it improves real study tasks.

For the present Cloudflare architecture, a Vectorize pilot avoids introducing another hosting platform. PostgreSQL with pgvector and full-text search is attractive if relational accounts, synchronized notes and other backend needs independently justify PostgreSQL. Thirteen available studies do not justify a distributed data platform by themselves.

Corpus pipeline:

1. Index canonical Markdown once; do not index Markdown, HTML and PDF copies as separate evidence. Resolve references through the rights/storage manifest. Exclude private submissions, private notes and unapproved material from the public index.
2. Chunk by headings and coherent argument boundaries. Experiment with roughly 300–800 tokens, keeping citations and definitions together. Preserve tables and adjacent context where needed.
3. Store document/version, section and passage IDs, title, language, source type, translation status, canonical URL, page or timestamp, and provenance. Distinguish primary texts, project studies, translations and unreviewed ASR.
4. Update incrementally from source hashes and remove superseded/deleted chunks. Apply authorization before retrieval if private collections are later introduced.
5. Combine lexical and vector candidates, optionally rerank, then show the actual passages. Keep generated explanation visually distinct from quotation. Treat retrieved text as data, never instructions.
6. Evaluate 50–100 expert-reviewed questions, including ambiguous, multilingual and unanswerable cases. Measure retrieval relevance, citation support, faithfulness, abstention and task success. Track embedding, query and answer-generation costs separately.

## Validation and rollout

Phase 1 requires automated regressions for mismatched/expired OAuth state, PKCE exchange, missing session storage, hostile request origins/content types, cache headers, repeated/expired magic links, active HTML/SVG, and the date parser. Rebuild generated readers from their source; preserve scholarly timestamps because this phase does not edit study content. Verify representative Draft and Released PDFs, including diagrams/math where present. Keep generated PDFs out of Git.

Ship through a reviewed PR. Deploy both API Workers and the static site together, confirm the existing KV/D1 bindings and secrets, and test real GitHub login/logout and email sign-in after deployment with an authorized test identity. Previously issued legacy cookies and pre-change magic links may require signing in again. Do not describe local mocks as production authentication verification.

For later UX phases, observe users finding a definition, comparing an argument, checking a source, resuming a study, and revising a submission. Measure task completion, time, search failures, resumed reading and draft recovery. Use those results to choose the next tools.

## Sources

- [GitHub OAuth authorization and PKCE](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
- [OWASP OAuth guidance](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP DOM XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [WCAG reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) and [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [Core Web Vitals thresholds](https://web.dev/articles/defining-core-web-vitals-thresholds)
- [Pagefind](https://pagefind.app/), [Vectorize metadata filters](https://developers.cloudflare.com/vectorize/reference/metadata-filtering/), and [pgvector hybrid search](https://github.com/pgvector/pgvector#hybrid-search)

## Phase 1 implementation record

Implemented on `codex/website-phase1-security-reader`; production rollout is pending PR review and merge.

- Signed, expiring OAuth state is compared before contacting GitHub, with S256 PKCE on authorization and exchange. GitHub tokens remain in required KV storage. Readable legacy session cookies are rejected.
- Both API Workers enforce trusted Origin and JSON on browser writes and apply private/no-store headers to every response. The authenticated machine notification endpoint retains its separate secret-based contract. My Submissions supplies JSON content type for bodyless writes too.
- Discussion magic links are stored as SHA-256 digests and consumed by one conditional SQL write. Existing D1 tables suffice; pre-change links require replacement.
- Author HTML passes a pinned HTML5 sanitizer before trusted reader chrome and KaTeX rendering. Static SVG validation rejects active content and external resources; metadata cannot close its JSON-LD script. Mermaid is pinned consistently to 11.17.2 in browser and PDF and uses strict security mode.
- PDF loading blocks network requests and unrelated local files. Browser scripts are disabled during initial document loading; the bundled strict diagram renderer runs afterwards. Chrome receives OS/locale variables instead of publishing credentials. This narrows the document-rendering boundary; it does not turn arbitrary contributor-modified CI scripts into trusted code.
- Reader Next works above the first section; section navigation records a link and moves focus; subsection and main-content anchors account for the toolbar. Light/dark canvas colors are explicit and diagrams redraw on theme changes. Long words and inline equations no longer widen the mobile page; mobile toolbar controls have 44-pixel heights.
- Catalog dates use an explicit IST parser for ordering and document version URLs. The 45 existing study/companion readers were rebuilt, and the full publishing pipeline produced one additional companion reader from its existing Markdown; no canonical study Markdown, status or Edited-on timestamp was changed.
- API CI tests and bundles both Workers, including changes in their shared request guard. Deployment is restricted to master. PDF build-selection rules include the new rendering-security helpers.
- Updated vulnerable Mermaid and compatible transitive dependencies, including both Workers' Wrangler tooling. Both Worker dependency audits report zero known vulnerabilities at validation time.

Validation completed locally: all 31 published Markdown-derived PDFs rebuilt and verified; all 36 enforced script suites; both Workers' real route tests and Wrangler dry-run bundles; catalog and agent-rule synchronization; static SVG validation; repeated byte-identical PDFs for a Draft, a Released study, and the formal study with math and eight diagrams. Browser checks cover 320/390-pixel reader reflow, theme selection, initial Next, subsection anchor clearance, and catalog date/title sorting. Production GitHub/email authentication still needs a post-deployment check with an authorized test identity.

Follow-up limits remain explicit: KV logout propagation is not instantaneous across locations; discussion cookies do not yet have per-session server-side revocation; full abuse controls and retention policy remain future work. The substantial reader workspace, resume/bookmarks, passage search, independent draft recovery, and vector retrieval remain Phases 2–6.

**Open dependency follow-up:** the Scripts audit still reports four high-severity package entries, all from the same `extract-zip` advisory through Puppeteer's browser installer. A malicious browser ZIP can contain unsafe symlinks. This is a build-tool dependency, and the document renderer does not accept ZIP archives; nevertheless, the dependency remains vulnerable. Keep browser acquisition restricted to the configured trusted source. Schedule a dedicated Puppeteer/toolchain upgrade next, with Node compatibility, the explicit Chrome pin, PDF reproducibility, pagination, math, diagrams and presentation tests verified together. The audit suggests Puppeteer 25.10.0, a major upgrade; this phase retains Puppeteer 24.43.1 and Chrome 148.0.7778.97 to preserve the established renderer contract. See the [extract-zip advisory](https://github.com/advisories/GHSA-jmr9-qjv8-65gv). This is a recorded residual risk, not an audit-clean claim.

Sanitizer implementation follows the [nh3 HTML5 sanitizer documentation](https://nh3.readthedocs.io/en/latest/).

## Phase 2 implementation record

Implemented on `codex/reader-essentials`, 6 September 2026, and merged in PR #400.

- **Contents beside the text:** a collapsible desktop panel follows the current heading and expands its section's subsections. Previous/Next and the current heading remain in the toolbar. The panel becomes a modal drawer on smaller screens, with keyboard tabs, Escape and focus restoration.
- **Reading comfort:** five text sizes, three line spacings, three column widths, and device/light/sepia/dark colors. Preferences survive reload and apply across study readers. Changing the type size or opening the desktop panel keeps the same passage in view.
- **Resume a passage:** save a paragraph identifier, its section, an excerpt and the position within the paragraph. An explicit Resume banner appears on return; a supplied deep link takes precedence. If text changes, recovery uses an unambiguous excerpt in the original section or opens that section with a notice. A missing passage is reported instead of guessing.
- **Named bookmarks:** add, revisit, rename and remove up to 100 places per document. Names and excerpts render as text. Autosave reads the latest stored bookmark collection, and other tabs receive updates. Confirmed cleanup removes only the current document's saved places.
- **Local storage:** no account or new service is required. Storage failures retain changes for the visit and explain that they cannot persist. Unreadable saved data is preserved until the reader deliberately clears it. These are device-local conveniences; clearing browser data removes them, and cross-device sync/export remain later work.
- **Shared delivery:** screen CSS and deferred JavaScript are separate reusable assets, versioned by their contents. All 46 tracked study and companion readers were regenerated. An enforced check catches stale asset references. These two screen-only assets do not invalidate PDF caches; changes to the markup helper still trigger the PDF verification workflows.

Validation: 31 published Markdown PDFs rebuilt through the internal pipeline. Draft, Released and formal/math/diagram samples remained byte-identical to their pre-change PDFs. Automated checks cover preference and stored-data validation, passage recovery after edits, ambiguous matches, navigation boundaries, control wiring, print isolation, asset synchronization and cache behavior. Chromium browser checks cover desktop and 320/390-pixel layouts, the largest text setting, theme persistence, section links, browser Back, explicit resume, bookmark renaming, cross-tab changes, keyboard drawer operation, unavailable/full storage, unreadable-data recovery and hostile bookmark labels.

Before calling this a complete accessibility or usability evaluation, test with screen-reader users and readers using Safari/Firefox and real mobile devices. Observe whether readers can resume and find an argument without assistance. Phase 3 should add passage search, citation previews and enlarged diagrams/tables; a vector database remains unnecessary for the reader essentials delivered here.

## Phase 3 implementation record

Implemented on `codex/reader-find-and-verify`, 6 September 2026. Publication awaits review and merge of this phase.

- **Find an argument:** the reader's Find tab searches words or quoted phrases within the open document. Results include the section and a highlighted excerpt; Previous/Next move between matching passages. Modern browsers highlight the matching words without replacing the document's text or breaking definitions, citations and equations. A passage outline remains available when word highlighting is unsupported.
- **Search the collection:** `Studies/search.html`, linked from Browse all studies and the reader, covers 13 published studies and 18 companion documents. Filter by document, study/note, status and language. All query words must occur in one passage. Latin diacritics are ignored; Hindi vowel signs and spelling are preserved. This is literal search, without inferred synonyms, translation or generated answers. Equation text is indexed once; raw Mermaid syntax is excluded.
- **Load only when needed:** opening a reader downloads no collection index. Collection search first loads a roughly 12 KB manifest, then fetches separate indexes for selected documents with four concurrent requests. Successful indexes are reused during the visit. The complete corpus is about 3 MB of JSON, about 0.85 MB with gzip; these are local artifact measurements, not production transfer or latency guarantees. Results are shown in batches. Aborted searches cannot replace newer results, and partial failures identify unavailable documents and permit retry.
- **Share a passage:** anchors exist in generated HTML before JavaScript and preserve Phase 2 bookmark IDs. Link & sources copies a canonical passage URL with its original section and source version. Unrelated edits leave the passage ID intact. Changed text produces a new ID; an obsolete link opens the original section with a notice when possible. This is recovery, not an archive of old versions.
- **Check a citation:** recognized source codes and bibliography links open the actual bibliography entry beside the selected passage. Readers can search the study's references, copy a citation, or open the source in a new tab. The preview does not fetch or summarize a source PDF and does not infer PDF page numbers from printed citations. Ambiguous source codes are not assigned automatically. Clipboard failures offer selectable text.
- **Read figures and tables:** Enlarge opens a modal viewer with zoom, Fit, 100% and scroll/swipe controls. Tables start at readable size, including on phones. Diagram IDs and internal references are isolated from the document. Closing the viewer restores the reading position and keyboard focus.
- **Keep publication consistent:** all 46 existing readers were regenerated. The converter updates only the changed document's index; catalog writes remove obsolete/unpublished entries. Verification rejects stale source versions, missing indexes, duplicate/mismatched inventory and stale generated search pages. Indexes contain public documents only. No account, search API, vector database or new hosting service is required. Screen asset and search-index edits preserve PDF-cache reuse; shared renderer changes still run PDF checks.

Validation includes all 31 published Markdown PDFs through the internal renderer, all 39 enforced script suites, the six additional reader-layout checks, reference integrity, catalog/search synchronization and agent-rule synchronization. Draft and Released text samples remain byte-identical to Phase 2. The 84-page formal study has a different PDF hash after adding diagram passage IDs, but every page's text and rendered pixels and the complete outline match the Phase 2 PDF; two repeat builds produce identical new bytes. Canonical study Markdown, scholarly timestamps and statuses are unchanged.

Chromium checks cover desktop and 320/390-pixel layouts, quoted queries, filters and result pagination, matching-passage clearance below the toolbar, source metadata and copying, focus restoration, enlarged Mermaid/table rendering, and partial index failure/retry. Real-device, Firefox/Safari and screen-reader usability checks remain necessary before claiming comprehensive accessibility or field performance. The complete reference library and multilingual semantic retrieval remain future work. A vector index is still unnecessary for these literal find-and-verify tasks; evaluate the hybrid-search pilot described above only when conceptual retrieval becomes a demonstrated need.
