---
name: cite-study
description: >-
  Cite Analytic Madhyasth Darshan studies from the canonical markdown,
  using catalog slugs, Edited-on timestamps, and glossary terms. Use when
  quoting, referencing, or attributing a paper from this collection.
---

# Cite a study

Prefer the study **markdown** over HTML or PDF. Catalog rows expose `md` (relative to `/Studies/`) or `mdUrl` from `GET /api/studies` and MCP `get_study`.

## What to record

1. **Title** and **slug** (directory name, for example `The-Ontology-of-Coexistence`).
2. **Status** (`draft` or `released`). Ongoing rows have no document yet.
3. **Edited on** from the study header, also as `updated` on the catalog row and as `date_modified` in https://analyticmadhyasthdarshan.org/Studies/feed.json
4. **Section** with a `§` cross-reference when the study uses numbered headings.
5. **URL** to the markdown or HTML on https://analyticmadhyasthdarshan.org

Example:

> Raghav Mohan, *The Ontology of Coexistence*, released, 29 July 2026. https://analyticmadhyasthdarshan.org/Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md

## Quoting

Quote the primary Madhyasth Darshan texts from local `References/` paths when those files are in the study bibliography. Do not treat this site's studies as primary sources for the darshan itself; they are analytic comparative papers.

Shared terms (`jeevan`, `satta`, `saha-astitva`, …) are defined in https://analyticmadhyasthdarshan.org/Studies/glossary.json. Use the glossary display form in running prose.

## Lookups

```
GET https://analyticmadhyasthdarshan.org/api/studies?slug=The-Ontology-of-Coexistence
GET https://analyticmadhyasthdarshan.org/Studies/catalog-all.json
```
