# Primer sources and generated PDFs

The book and its plan are maintained here, separately from the Studies and
Applications publication pipeline. Markdown, the image assets and the Python
renderers are the authoring inputs. PDFs are generated files and are ignored by
Git; they remain available locally after a build.

| Markdown source | Generated PDF |
| --- | --- |
| [Book manuscript](madhyasth-darshan-primer.md) | `madhyasth-darshan-primer.pdf` |
| [Book plan](madhyasth-darshan-primer-book-plan.md) | `madhyasth-darshan-primer-book-plan-revised.pdf` |

## Build both PDFs

From the repository root, install the standalone renderer dependencies once:

```powershell
python -m pip install -r Primer/requirements.txt
```

Then regenerate both PDFs whenever their Markdown, images or renderer changes:

```powershell
python Primer/build_pdfs.py
```

To rebuild only one document:

```powershell
python Primer/build_pdfs.py book
python Primer/build_pdfs.py plan
```

The book uses a 6-by-9-inch layout; the plan uses A4. Both renderers preserve Hindi
shaping and use the Georgia and Mangal fonts installed in `C:/Windows/Fonts`.
Another machine can supply `--font-dir` pointing to a directory containing
`georgia.ttf`, `georgiab.ttf`, `georgiai.ttf`, `georgiaz.ttf`, `mangal.ttf` and
`mangalb.ttf`. Fonts are not copied into this repository.

Optional `--vendor` supplies an existing directory of installed Python packages.
Optional `--output-dir` writes the PDFs elsewhere, which is useful for verification
without replacing local copies. Each renderer reports its source and PDF hashes
and page count; its individual command also accepts `--report` to save that record.

This command generates the files on demand. There is no background watcher or
Primer GitHub Actions PDF build configured. After content or layout changes,
check text completeness and inspect the rendered pages before sharing the PDFs.

Book development and review work is tracked only in [PENDING.md](../PENDING.md).
