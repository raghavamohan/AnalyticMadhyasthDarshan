---
name: cite-study
description: >-
  Cite Analytic Madhyasth Darshan studies from the canonical markdown,
  using catalog slugs, Edited-on timestamps, and glossary terms. Use when
  quoting, referencing, or attributing a paper from this collection.
---

# Cite a study

Prefer the study **markdown** over HTML or PDF. Catalog rows expose `md` (relative to `/Studies/`) or `mdUrl` from `GET /api/studies/{slug}` and MCP `get_study`. Use `GET /api/cite/{slug}` for a suggested citation line that already includes title, status, Edited-on, and the markdown URL.

## What to record

1. **Title** and **slug** (directory name, for example `The-Ontology-of-Coexistence`).
2. **Status** (`draft` or `released`). Ongoing/Planned rows have no public
   document link and should not be cited as a study; an approved proposal may
   still have internal stub artifacts.
3. **Edited on** from the study header, also as `updated` on the catalog row and as `date_modified` in https://analyticmadhyasthdarshan.org/Studies/feed.json
4. **Section** with a `§` cross-reference when the study uses numbered headings.
5. **URL** to the markdown or HTML on https://analyticmadhyasthdarshan.org

Retrieve current citation metadata from `/api/cite/{slug}` rather than copying
a fixed example date or status. Follow the returned `mdUrl` or `url`, retaining
its publication-revision query parameter when present.

## Quoting

For claims about the primary Madhyasth Darshan texts, follow the study's
bibliography and inspect the cited source before quoting it. A `References/`
URL may be served from R2 and need not exist in a local clone. Do not treat this
site's analytic comparative studies as primary texts of the darshan.

Shared terms (`jeevan`, `satta`, `saha-astitva`, …) are defined in https://analyticmadhyasthdarshan.org/Studies/glossary.json. Use the glossary display form in running prose.

## Lookups

```
GET https://analyticmadhyasthdarshan.org/api/cite/The-Ontology-of-Coexistence
GET https://analyticmadhyasthdarshan.org/api/studies/The-Ontology-of-Coexistence
GET https://analyticmadhyasthdarshan.org/Studies/catalog-all.json
```
