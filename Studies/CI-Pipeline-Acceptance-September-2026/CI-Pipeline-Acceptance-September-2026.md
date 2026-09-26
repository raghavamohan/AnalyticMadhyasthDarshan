# CI Pipeline Acceptance September 2026

**Author:** Raghava Mohan

**Edited on:** September 27, 2026, 12:41 AM IST
**Status:** Released

Can a reviewed source change reach the public catalog, API, HTML reader and PDF as one coherent revision? This temporary maintainer document supplies a controlled input for that question. It exists solely to verify CI workitem R2 and will be retired after the acceptance exercise. It makes no philosophical claim and uses no primary text, quotation or external research reference.

## 1. Publication consistency

A reader needs the title, lifecycle status and document content to describe the same approved source. A catalog that advertises a new draft while serving an older PDF would give the reader conflicting information. The protected publication workflow therefore builds or reuses verified outputs, binds their checksums to a release manifest, audits a staged candidate and then promotes that complete revision.

The acceptance exercise observes this document first as a Planned entry, then as a Draft with a reader and a watermarked PDF. A later content revision supplies a distinct source checksum while preserving Draft status. Changing the document to Released must remove the Draft watermark and update the metadata in the public catalog and API together.

This content revision adds a distinct acceptance marker: PUBLIC-LIFECYCLE-REVISION-2. A reader opened from the older dashboard must show this paragraph and the new publication revision together.

## 2. Reader and dashboard navigation

An already open reader belongs to the revision it loaded. Its internal document links should remain consistent with that revision when a newer publication appears. Saved offline content should also remain readable without combining an old document with resources from another release. Separate deployed browser checks exercise those properties with the shipped service worker.

The authenticated dashboard serves a different purpose: it reports the current public result of a contributor's reviewed work. Its Live link must therefore open the newly published revision even when the dashboard itself was opened earlier. The public exercise keeps an older dashboard open through the content revision and checks the resulting Live destination.

## 3. Retirement and retained history

Retirement removes this temporary fixture from the active catalog, API inventory and canonical reader and PDF paths. Its proposal and source changes remain recoverable in repository history. Previously published immutable releases remain available under the publication retention policy; ordinary retirement does not authorize an R2 purge.

Success is established from the observed public responses, verified release receipts and authenticated dashboard state after each protected publication. This document describes the test input and expected behavior. The permanent acceptance record stores the actual results so that this temporary source can be retired without losing the evidence.
