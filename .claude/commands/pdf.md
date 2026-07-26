---
description: Open a study PDF in the Browser pane
argument-hint: [study slug, filename, or path — omit to list all]
allowed-tools: Glob, mcp__Claude_Browser__preview_start, mcp__Claude_Browser__computer
---

Open the PDF matching `$ARGUMENTS` in the Browser pane.

Claude Code's file explorer cannot preview PDFs ("Inline preview isn't available
for this file"), and that behaviour is not configurable. The Browser pane renders
them fine. This command bridges the two.

## Steps

1. Find candidate PDFs with Glob: `Studies/**/*.pdf`, `Applications/**/*.pdf`,
   `References/**/*.pdf`. Match `$ARGUMENTS` case-insensitively against the full
   path, so a study slug, a bare filename, or a fragment all work.
2. Resolve:
   - **No argument** — list every study PDF as clickable markdown links, grouped
     by directory, and stop. Do not open anything.
   - **One match** — open it.
   - **Several matches** — list them as clickable markdown links and ask which.
     Do not guess.
   - **No match** — say so plainly and show the nearest names.
3. Open by calling `preview_start` with a `file:///` URL built from the absolute
   path: forward slashes, and spaces percent-encoded as `%20`. For example
   `file:///E:/Madhyasth%20Darshan/Studies/<Slug>/<Slug>.pdf`.
4. Screenshot the pane to confirm it rendered, then report the page count and
   the resolved path.

## Notes

- Prefer `<Slug>/<Slug>.pdf` when a directory holds several PDFs (companion
  decks, research notes, comparison papers) and the argument names only the
  study — mention the siblings you skipped.
- Files outside the project folder render as static snapshots.
- To read a PDF's text rather than view it, use the Read tool or `pdftotext`;
  this command is for looking at rendered layout.
